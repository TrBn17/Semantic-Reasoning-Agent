from datetime import datetime, timezone
from collections import defaultdict
from uuid import uuid4

from sqlalchemy import delete, desc, func, select
from sqlalchemy.orm import selectinload

from semantic_reasoning_agent.core.config import Settings
from semantic_reasoning_agent.domain.contracts.published_ontology_snapshot import PublishedOntologySnapshot
from semantic_reasoning_agent.infrastructure.graphiti.graphiti_gateway import GraphitiGateway
from semantic_reasoning_agent.persistence.database import DatabaseManager
from semantic_reasoning_agent.persistence.models import (
    DocumentChunkORM,
    DocumentORM,
    OntologyBuildORM,
    OntologyBuildStepORM,
    OntologyCandidateEntityORM,
    OntologyCandidateRelationORM,
    OntologyEntityORM,
    OntologyEntityTypeDefinitionORM,
    OntologyRelationORM,
    OntologyRelationTypeDefinitionORM,
    OntologyVersionORM,
)
from semantic_reasoning_agent.domain.ontology.models import ExtractedEntity, ExtractedRelation
from semantic_reasoning_agent.domain.ontology.models import OntologySourceChunk
from semantic_reasoning_agent.domain.ontology.pipeline_steps import ONTOLOGY_BUILD_STEP_NAMES
from semantic_reasoning_agent.ports.ontology_extractor import OntologyExtractorPort
from semantic_reasoning_agent.schemas.documents import DocumentStatus
from semantic_reasoning_agent.schemas.ontology import (
    OntologyBuildCreateRequest,
    OntologyBuildResponse,
    OntologyBuildStatus,
    OntologyBuildStepResponse,
    OntologyCandidateEntityResponse,
    OntologyCandidateRelationResponse,
    OntologyEntityTypeDefinitionResponse,
    OntologyEntityResponse,
    OntologyGraphResponse,
    OntologyRelationTypeDefinitionResponse,
    OntologyPublishResponse,
    OntologyRelationResponse,
    OntologyReviewAction,
    OntologyReviewStatus,
    OntologyStepStatus,
    OntologyVersionResponse,
)
from semantic_reasoning_agent.services.ontology_graph_publisher import (
    OntologyGraphPublisher,
    OntologyGraphPublisherError,
)
from semantic_reasoning_agent.workers.task_dispatcher import TaskDispatcher


def utc_now() -> datetime:
    return datetime.now(timezone.utc)

class OntologyBuildNotFoundError(ValueError):
    """Raised when an ontology build id does not exist."""


class OntologyCandidateNotFoundError(ValueError):
    """Raised when an ontology candidate id does not exist."""


class OntologyBuildError(ValueError):
    """Raised when an ontology build cannot be created or processed."""


class OntologyPublishError(ValueError):
    """Raised when an ontology build cannot be published."""


class OntologyGraphError(ValueError):
    """Raised when the published graph cannot be read."""


class OntologyService:
    def __init__(
        self,
        settings: Settings,
        database_manager: DatabaseManager,
        task_dispatcher: TaskDispatcher,
        graphiti_gateway: GraphitiGateway,
        ontology_extractor: OntologyExtractorPort,
    ) -> None:
        self._settings = settings
        self._database_manager = database_manager
        self._task_dispatcher = task_dispatcher
        self._graphiti_gateway = graphiti_gateway
        self._graph_publisher = OntologyGraphPublisher(graphiti_gateway)
        self._ontology_extractor = ontology_extractor

    def create_build(self, request: OntologyBuildCreateRequest) -> OntologyBuildResponse:
        with self._database_manager.session() as session:
            document = session.get(DocumentORM, request.document_id)
            if document is None:
                raise OntologyBuildError(f"Document '{request.document_id}' was not found.")
            if document.status != DocumentStatus.indexed.value:
                raise OntologyBuildError(
                    f"Document '{request.document_id}' must be indexed before ontology extraction starts."
                )

            build_id = str(uuid4())
            timestamp = utc_now()
            session.add(
                OntologyBuildORM(
                    id=build_id,
                    document_id=document.id,
                    workspace_id=request.workspace_id or document.workspace_id,
                    status=OntologyBuildStatus.pending.value,
                    domain=None,
                    created_at=timestamp,
                    started_at=None,
                    finished_at=None,
                    updated_at=timestamp,
                    error_message=None,
                    published_version_id=None,
                )
            )
            session.add_all(self._build_step_records(build_id))

        self._queue_build(build_id)
        return self.get_build(build_id)

    def list_builds(self, workspace_id: str | None = None) -> list[OntologyBuildResponse]:
        resolved_workspace_id = workspace_id or self._settings.default_workspace_id
        with self._database_manager.session() as session:
            builds = session.scalars(
                select(OntologyBuildORM)
                .where(OntologyBuildORM.workspace_id == resolved_workspace_id)
                .order_by(desc(OntologyBuildORM.created_at))
            ).all()
            return self._to_build_schemas(session, builds)

    def get_build(self, build_id: str) -> OntologyBuildResponse:
        with self._database_manager.session() as session:
            build = session.scalar(
                select(OntologyBuildORM).where(OntologyBuildORM.id == build_id)
            )
            if build is None:
                raise OntologyBuildNotFoundError(f"Ontology build '{build_id}' was not found.")
            return self._to_build_schemas(session, [build])[0]

    def list_build_entities(
        self,
        build_id: str,
        status: OntologyReviewStatus | None = None,
    ) -> list[OntologyCandidateEntityResponse]:
        self._ensure_build_exists(build_id)
        with self._database_manager.session() as session:
            statement = select(OntologyCandidateEntityORM).where(
                OntologyCandidateEntityORM.build_id == build_id
            )
            if status is not None:
                statement = statement.where(OntologyCandidateEntityORM.status == status.value)
            entities = session.scalars(statement).all()
            entities.sort(key=lambda entity: entity.canonical_name.lower())
            return [self._to_candidate_entity_schema(entity) for entity in entities]

    def list_build_relations(
        self,
        build_id: str,
        status: OntologyReviewStatus | None = None,
    ) -> list[OntologyCandidateRelationResponse]:
        self._ensure_build_exists(build_id)
        with self._database_manager.session() as session:
            statement = select(OntologyCandidateRelationORM).where(
                OntologyCandidateRelationORM.build_id == build_id
            )
            if status is not None:
                statement = statement.where(OntologyCandidateRelationORM.status == status.value)
            relations = session.scalars(statement).all()
            relations.sort(
                key=lambda relation: (
                    relation.relation_type,
                    relation.source_name.lower(),
                    relation.target_name.lower(),
                )
            )
            return [self._to_candidate_relation_schema(relation) for relation in relations]

    def review_entity(
        self,
        entity_id: str,
        action: OntologyReviewAction,
    ) -> OntologyCandidateEntityResponse:
        with self._database_manager.session() as session:
            entity = session.get(OntologyCandidateEntityORM, entity_id)
            if entity is None:
                raise OntologyCandidateNotFoundError(f"Ontology entity candidate '{entity_id}' was not found.")
            entity.status = self._status_from_action(action)
            entity.updated_at = utc_now()
            build = session.get(OntologyBuildORM, entity.build_id)
            if build is not None:
                build.updated_at = utc_now()
        return self.get_entity(entity_id)

    def review_relation(
        self,
        relation_id: str,
        action: OntologyReviewAction,
    ) -> OntologyCandidateRelationResponse:
        with self._database_manager.session() as session:
            relation = session.get(OntologyCandidateRelationORM, relation_id)
            if relation is None:
                raise OntologyCandidateNotFoundError(
                    f"Ontology relation candidate '{relation_id}' was not found."
                )
            relation.status = self._status_from_action(action)
            relation.updated_at = utc_now()
            build = session.get(OntologyBuildORM, relation.build_id)
            if build is not None:
                build.updated_at = utc_now()
        return self.get_relation(relation_id)

    def get_entity(self, entity_id: str) -> OntologyCandidateEntityResponse:
        with self._database_manager.session() as session:
            entity = session.get(OntologyCandidateEntityORM, entity_id)
            if entity is None:
                raise OntologyCandidateNotFoundError(f"Ontology entity candidate '{entity_id}' was not found.")
            return self._to_candidate_entity_schema(entity)

    def get_relation(self, relation_id: str) -> OntologyCandidateRelationResponse:
        with self._database_manager.session() as session:
            relation = session.get(OntologyCandidateRelationORM, relation_id)
            if relation is None:
                raise OntologyCandidateNotFoundError(
                    f"Ontology relation candidate '{relation_id}' was not found."
                )
            return self._to_candidate_relation_schema(relation)

    def publish_build(self, build_id: str) -> OntologyPublishResponse:
        build_response = self.get_build(build_id)
        if build_response.status not in {
            OntologyBuildStatus.completed,
            OntologyBuildStatus.published,
        }:
            raise OntologyPublishError(
                f"Ontology build '{build_id}' must complete before it can be published."
            )

        snapshot = self._prepare_published_snapshot(build_id)
        try:
            self._graph_publisher.publish(snapshot)
        except OntologyGraphPublisherError as exc:
            raise OntologyPublishError(str(exc)) from exc

        with self._database_manager.session() as session:
            build = session.get(OntologyBuildORM, build_id)
            if build is None:
                raise OntologyBuildNotFoundError(f"Ontology build '{build_id}' was not found.")
            build.status = OntologyBuildStatus.published.value
            build.published_version_id = snapshot.version.id
            build.updated_at = utc_now()

        return OntologyPublishResponse(
            build=self.get_build(build_id),
            version=snapshot.version,
        )

    def get_graph(self, workspace_id: str | None = None) -> OntologyGraphResponse:
        resolved_workspace_id = workspace_id or self._settings.default_workspace_id
        return self._get_relational_graph(resolved_workspace_id)

    def process_build(self, build_id: str) -> None:
        build = self._get_build_record(build_id)
        chunks = self._get_document_chunks(build.document_id)
        if not chunks:
            raise OntologyBuildError(
                f"Document '{build.document_id}' does not have indexed chunks for ontology extraction."
            )

        self._reset_build(build_id)
        self._mark_build_running(build_id)
        try:
            extraction_run_id = str(uuid4())
            self._mark_step_running(build_id, "classify_document_domain")
            domain = self._ontology_extractor.classify_document_domain(chunks)
            self._mark_step_completed(
                build_id,
                "classify_document_domain",
                detail=f"Detected document domain '{domain}'.",
            )
            self._update_build_state(build_id, status=OntologyBuildStatus.running.value, domain=domain)

            self._mark_step_running(build_id, "extract_entities")
            extraction = self._ontology_extractor.extract_ontology_candidates(
                chunks,
                workspace_id=build.workspace_id,
            )
            entity_id_map = self._replace_candidate_entities(
                build,
                extraction.entities,
                extraction_run_id=extraction_run_id,
            )
            self._mark_step_completed(
                build_id,
                "extract_entities",
                detail=f"Extracted {len(extraction.entities)} candidate entities.",
            )

            self._mark_step_running(build_id, "extract_relations")
            self._replace_candidate_relations(
                build,
                extraction.relations,
                entity_id_map,
                extraction_run_id=extraction_run_id,
            )
            self._mark_step_completed(
                build_id,
                "extract_relations",
                detail=f"Extracted {len(extraction.relations)} candidate relations.",
            )

            self._mark_step_running(build_id, "resolve_entities")
            self._mark_step_completed(
                build_id,
                "resolve_entities",
                detail=f"Resolved {len(extraction.entities)} canonical entities.",
            )

            self._mark_step_running(build_id, "build_graph_upsert_plan")
            self._mark_step_completed(
                build_id,
                "build_graph_upsert_plan",
                detail=(
                    "Review queue is ready with "
                    f"{len(extraction.entities)} entities and {len(extraction.relations)} relations."
                ),
            )

            self._mark_step_running(build_id, "sync_neo4j")
            sync_detail = (
                "Neo4j is disabled; publish will keep the relational snapshot as the source of truth."
            )
            if self._graph_publisher.is_enabled():
                self._graph_publisher.publish()
                sync_detail = "Graphiti runtime graph is enabled; publish will refresh runtime graph indices."
            self._mark_step_completed(
                build_id,
                "sync_neo4j",
                detail=sync_detail,
            )

            self._update_build_state(
                build_id,
                status=OntologyBuildStatus.completed.value,
                domain=domain,
                finished_at=utc_now(),
                error_message=None,
            )
        except Exception as exc:
            self._mark_failed(build_id, self._active_step_name(build_id), str(exc))
            raise OntologyBuildError(str(exc)) from exc

    def _queue_build(self, build_id: str) -> None:
        try:
            self._task_dispatcher.enqueue_ontology_build_processing(build_id)
        except Exception as exc:
            raise OntologyBuildError(
                f"Failed to queue ontology build '{build_id}' for processing."
            ) from exc

    def _ensure_build_exists(self, build_id: str) -> None:
        with self._database_manager.session() as session:
            if session.get(OntologyBuildORM, build_id) is None:
                raise OntologyBuildNotFoundError(f"Ontology build '{build_id}' was not found.")

    def _get_build_record(self, build_id: str) -> OntologyBuildORM:
        with self._database_manager.session() as session:
            build = session.get(OntologyBuildORM, build_id)
            if build is None:
                raise OntologyBuildNotFoundError(f"Ontology build '{build_id}' was not found.")
            return OntologyBuildORM(
                id=build.id,
                document_id=build.document_id,
                workspace_id=build.workspace_id,
                status=build.status,
                domain=build.domain,
                created_at=build.created_at,
                started_at=build.started_at,
                finished_at=build.finished_at,
                updated_at=build.updated_at,
                error_message=build.error_message,
                published_version_id=build.published_version_id,
            )

    def _get_document_chunks(self, document_id: str) -> list[OntologySourceChunk]:
        with self._database_manager.session() as session:
            chunks = session.scalars(
                select(DocumentChunkORM)
                .where(DocumentChunkORM.document_id == document_id)
                .order_by(DocumentChunkORM.chunk_index)
            ).all()
            return [
                OntologySourceChunk(
                    chunk_id=chunk.chunk_id,
                    text=chunk.text,
                )
                for chunk in chunks
            ]

    def _reset_build(self, build_id: str) -> None:
        with self._database_manager.session() as session:
            build = session.get(OntologyBuildORM, build_id)
            if build is None:
                raise OntologyBuildNotFoundError(f"Ontology build '{build_id}' was not found.")
            build.status = OntologyBuildStatus.pending.value
            build.error_message = None
            build.domain = None
            build.started_at = None
            build.finished_at = None
            build.updated_at = utc_now()
            session.execute(
                delete(OntologyCandidateRelationORM).where(
                    OntologyCandidateRelationORM.build_id == build_id
                )
            )
            session.execute(
                delete(OntologyCandidateEntityORM).where(
                    OntologyCandidateEntityORM.build_id == build_id
                )
            )
            for step in session.scalars(
                select(OntologyBuildStepORM).where(OntologyBuildStepORM.build_id == build_id)
            ).all():
                step.status = OntologyStepStatus.pending.value
                step.detail = None
                step.started_at = None
                step.finished_at = None

    def _mark_build_running(self, build_id: str) -> None:
        with self._database_manager.session() as session:
            build = session.get(OntologyBuildORM, build_id)
            if build is None:
                raise OntologyBuildNotFoundError(f"Ontology build '{build_id}' was not found.")
            now = utc_now()
            build.status = OntologyBuildStatus.running.value
            build.started_at = now
            build.finished_at = None
            build.updated_at = now
            build.error_message = None

    def _update_build_state(
        self,
        build_id: str,
        *,
        status: str,
        domain: str | None = None,
        finished_at: datetime | None = None,
        error_message: str | None = None,
    ) -> None:
        with self._database_manager.session() as session:
            build = session.get(OntologyBuildORM, build_id)
            if build is None:
                raise OntologyBuildNotFoundError(f"Ontology build '{build_id}' was not found.")
            build.status = status
            build.updated_at = utc_now()
            build.error_message = error_message
            if domain is not None:
                build.domain = domain
            if finished_at is not None:
                build.finished_at = finished_at

    def _mark_failed(self, build_id: str, failed_step: str, error_message: str) -> None:
        timestamp = utc_now()
        with self._database_manager.session() as session:
            build = session.get(OntologyBuildORM, build_id)
            if build is None:
                raise OntologyBuildNotFoundError(f"Ontology build '{build_id}' was not found.")
            build.status = OntologyBuildStatus.failed.value
            build.error_message = error_message
            build.finished_at = timestamp
            build.updated_at = timestamp

            steps = session.scalars(
                select(OntologyBuildStepORM).where(OntologyBuildStepORM.build_id == build_id)
            ).all()
            step_map = {step.name: step for step in steps}
            failure_reached = False
            for name in ONTOLOGY_BUILD_STEP_NAMES:
                step = step_map.get(name)
                if step is None:
                    step = OntologyBuildStepORM(
                        id=f"{build_id}:{name}",
                        build_id=build_id,
                        name=name,
                        status=OntologyStepStatus.pending.value,
                        detail=None,
                        started_at=None,
                        finished_at=None,
                    )
                    session.add(step)
                if name == failed_step:
                    failure_reached = True
                    step.status = OntologyStepStatus.failed.value
                    step.detail = error_message
                    step.started_at = timestamp
                    step.finished_at = timestamp
                elif failure_reached:
                    step.status = OntologyStepStatus.pending.value
                    step.detail = None
                    step.started_at = None
                    step.finished_at = None
                else:
                    step.status = OntologyStepStatus.completed.value
                    step.started_at = timestamp
                    step.finished_at = timestamp

    def _mark_step_running(self, build_id: str, name: str) -> None:
        with self._database_manager.session() as session:
            step = self._get_step(session, build_id, name)
            now = utc_now()
            step.status = OntologyStepStatus.running.value
            step.started_at = now
            step.finished_at = None
            step.detail = None

    def _mark_step_completed(self, build_id: str, name: str, detail: str | None = None) -> None:
        with self._database_manager.session() as session:
            step = self._get_step(session, build_id, name)
            now = utc_now()
            step.status = OntologyStepStatus.completed.value
            if step.started_at is None:
                step.started_at = now
            step.finished_at = now
            step.detail = detail

    def _active_step_name(self, build_id: str) -> str:
        with self._database_manager.session() as session:
            steps = session.scalars(
                select(OntologyBuildStepORM).where(OntologyBuildStepORM.build_id == build_id)
            ).all()
            for name in reversed(ONTOLOGY_BUILD_STEP_NAMES):
                for step in steps:
                    if step.name == name and step.status == OntologyStepStatus.running.value:
                        return name
        return ONTOLOGY_BUILD_STEP_NAMES[0]

    def _replace_candidate_entities(
        self,
        build: OntologyBuildORM,
        entities: list[ExtractedEntity],
        *,
        extraction_run_id: str,
    ) -> dict[str, str]:
        entity_id_map: dict[str, str] = {}
        with self._database_manager.session() as session:
            session.execute(
                delete(OntologyCandidateEntityORM).where(
                    OntologyCandidateEntityORM.build_id == build.id
                )
            )
            timestamp = utc_now()
            for entity in entities:
                entity_id = str(uuid4())
                entity_id_map[entity.resolution_key] = entity_id
                session.add(
                    OntologyCandidateEntityORM(
                        id=entity_id,
                        build_id=build.id,
                        document_id=build.document_id,
                        workspace_id=build.workspace_id,
                        name=entity.name,
                        canonical_name=entity.canonical_name,
                        resolution_key=entity.resolution_key,
                        entity_type=entity.entity_type,
                        confidence=entity.confidence,
                        status=OntologyReviewStatus.pending_review.value,
                        source_chunk_id=entity.source_chunk_id,
                        evidence_text=entity.evidence_text,
                        provenance={
                            **entity.provenance,
                            "run_id": extraction_run_id,
                            "build_id": build.id,
                            "prompt_version": self._settings.ontology_prompt_version,
                        },
                        aliases=sorted(entity.aliases),
                        merged_into_entity_id=None,
                        created_at=timestamp,
                        updated_at=timestamp,
                    )
                )
        return entity_id_map

    def _replace_candidate_relations(
        self,
        build: OntologyBuildORM,
        relations: list[ExtractedRelation],
        entity_id_map: dict[str, str],
        *,
        extraction_run_id: str,
    ) -> None:
        with self._database_manager.session() as session:
            session.execute(
                delete(OntologyCandidateRelationORM).where(
                    OntologyCandidateRelationORM.build_id == build.id
                )
            )
            timestamp = utc_now()
            for relation in relations:
                session.add(
                    OntologyCandidateRelationORM(
                        id=str(uuid4()),
                        build_id=build.id,
                        document_id=build.document_id,
                        workspace_id=build.workspace_id,
                        source_entity_id=entity_id_map.get(relation.source_resolution_key),
                        target_entity_id=entity_id_map.get(relation.target_resolution_key),
                        source_name=relation.source_name,
                        target_name=relation.target_name,
                        relation_type=relation.relation_type,
                        confidence=relation.confidence,
                        status=OntologyReviewStatus.pending_review.value,
                        source_chunk_id=relation.source_chunk_id,
                        evidence_text=relation.evidence_text,
                        provenance={
                            **relation.provenance,
                            "run_id": extraction_run_id,
                            "build_id": build.id,
                            "prompt_version": self._settings.ontology_prompt_version,
                        },
                        created_at=timestamp,
                        updated_at=timestamp,
                    )
                )

    def _prepare_published_snapshot(self, build_id: str) -> PublishedOntologySnapshot:
        version_timestamp = utc_now()
        with self._database_manager.session() as session:
            build = session.scalar(
                select(OntologyBuildORM)
                .options(
                    selectinload(OntologyBuildORM.entities),
                    selectinload(OntologyBuildORM.relations),
                )
                .where(OntologyBuildORM.id == build_id)
            )
            if build is None:
                raise OntologyBuildNotFoundError(f"Ontology build '{build_id}' was not found.")

            approved_entities = [
                entity
                for entity in build.entities
                if entity.status == OntologyReviewStatus.approved.value
                and entity.merged_into_entity_id is None
            ]
            if not approved_entities:
                raise OntologyPublishError(
                    f"Ontology build '{build_id}' has no approved entities to publish."
                )

            existing_version = None
            if build.published_version_id is not None:
                existing_version = session.scalar(
                    select(OntologyVersionORM)
                    .options(
                        selectinload(OntologyVersionORM.entities),
                        selectinload(OntologyVersionORM.entity_types),
                        selectinload(OntologyVersionORM.relations),
                        selectinload(OntologyVersionORM.relation_types),
                    )
                    .where(OntologyVersionORM.id == build.published_version_id)
                )
            if existing_version is not None:
                return PublishedOntologySnapshot(
                    workspace_id=build.workspace_id,
                    version=self._to_version_schema(existing_version),
                    entity_type_definitions=[
                        self._to_entity_type_definition_schema(entity_type)
                        for entity_type in existing_version.entity_types
                    ],
                    relation_type_definitions=[
                        self._to_relation_type_definition_schema(relation_type)
                        for relation_type in existing_version.relation_types
                    ],
                    entities=[self._to_entity_schema(entity) for entity in existing_version.entities],
                    relations=[self._to_relation_schema(relation) for relation in existing_version.relations],
                )

            stale_versions = session.scalars(
                select(OntologyVersionORM)
                .options(
                    selectinload(OntologyVersionORM.entities),
                    selectinload(OntologyVersionORM.entity_types),
                    selectinload(OntologyVersionORM.relations),
                    selectinload(OntologyVersionORM.relation_types),
                )
                .where(OntologyVersionORM.source_build_id == build.id)
            ).all()
            for stale_version in stale_versions:
                session.delete(stale_version)

            latest_version = session.scalar(
                select(OntologyVersionORM)
                .where(OntologyVersionORM.workspace_id == build.workspace_id)
                .order_by(desc(OntologyVersionORM.version_number))
            )
            next_version_number = 1 if latest_version is None else latest_version.version_number + 1
            version_id = str(uuid4())
            version = OntologyVersionORM(
                id=version_id,
                workspace_id=build.workspace_id,
                version_number=next_version_number,
                source_build_id=build.id,
                created_at=version_timestamp,
            )
            session.add(version)

            entity_type_definitions = self._build_entity_type_definitions(
                workspace_id=build.workspace_id,
                version_id=version_id,
                entities=approved_entities,
                created_at=version_timestamp,
            )
            relation_type_definitions = self._build_relation_type_definitions(
                workspace_id=build.workspace_id,
                version_id=version_id,
                entities=approved_entities,
                relations=[
                    relation
                    for relation in build.relations
                    if relation.status == OntologyReviewStatus.approved.value
                ],
                created_at=version_timestamp,
            )
            for entity_type_definition in entity_type_definitions:
                session.add(entity_type_definition)
            for relation_type_definition in relation_type_definitions:
                session.add(relation_type_definition)

            version_entities: list[OntologyEntityResponse] = []
            published_entity_ids: dict[str, str] = {}
            for entity in approved_entities:
                published_entity_id = str(uuid4())
                published_entity_ids[entity.id] = published_entity_id
                published_entity = OntologyEntityORM(
                    id=published_entity_id,
                    version_id=version_id,
                    workspace_id=build.workspace_id,
                    resolution_key=entity.resolution_key,
                    name=entity.canonical_name,
                    entity_type=entity.entity_type,
                    aliases=sorted(set(entity.aliases or [])),
                    source_build_id=build.id,
                    source_document_id=build.document_id,
                    created_at=version_timestamp,
                )
                session.add(published_entity)
                version_entities.append(self._to_entity_schema(published_entity))

            version_relations: list[OntologyRelationResponse] = []
            for relation in build.relations:
                if relation.status != OntologyReviewStatus.approved.value:
                    continue
                source_entity_id = published_entity_ids.get(relation.source_entity_id or "")
                target_entity_id = published_entity_ids.get(relation.target_entity_id or "")
                if source_entity_id is None or target_entity_id is None:
                    continue
                published_relation = OntologyRelationORM(
                    id=str(uuid4()),
                    version_id=version_id,
                    workspace_id=build.workspace_id,
                    source_entity_id=source_entity_id,
                    target_entity_id=target_entity_id,
                    relation_type=relation.relation_type,
                    confidence=relation.confidence,
                    source_build_id=build.id,
                    source_document_id=build.document_id,
                    evidence_text=relation.evidence_text,
                    provenance=relation.provenance,
                    created_at=version_timestamp,
                )
                session.add(published_relation)
                version_relations.append(self._to_relation_schema(published_relation))

            version_schema = OntologyVersionResponse(
                id=version_id,
                workspace_id=build.workspace_id,
                version_number=next_version_number,
                source_build_id=build.id,
                created_at=version_timestamp,
                entity_type_count=len(entity_type_definitions),
                relation_type_count=len(relation_type_definitions),
                entity_count=len(version_entities),
                relation_count=len(version_relations),
            )
            return PublishedOntologySnapshot(
                workspace_id=build.workspace_id,
                version=version_schema,
                entity_type_definitions=[
                    self._to_entity_type_definition_schema(entity_type_definition)
                    for entity_type_definition in entity_type_definitions
                ],
                relation_type_definitions=[
                    self._to_relation_type_definition_schema(relation_type_definition)
                    for relation_type_definition in relation_type_definitions
                ],
                entities=version_entities,
                relations=version_relations,
            )

    def _get_relational_graph(self, workspace_id: str) -> OntologyGraphResponse:
        with self._database_manager.session() as session:
            version = session.scalar(
                select(OntologyVersionORM)
                .options(
                    selectinload(OntologyVersionORM.entities),
                    selectinload(OntologyVersionORM.entity_types),
                    selectinload(OntologyVersionORM.relations),
                    selectinload(OntologyVersionORM.relation_types),
                )
                .where(OntologyVersionORM.workspace_id == workspace_id)
                .order_by(desc(OntologyVersionORM.version_number))
            )
            if version is None:
                return OntologyGraphResponse(workspace_id=workspace_id)
            return OntologyGraphResponse(
                workspace_id=workspace_id,
                version=self._to_version_schema(version),
                entity_type_definitions=[
                    self._to_entity_type_definition_schema(entity_type)
                    for entity_type in version.entity_types
                ],
                relation_type_definitions=[
                    self._to_relation_type_definition_schema(relation_type)
                    for relation_type in version.relation_types
                ],
                entities=[self._to_entity_schema(entity) for entity in version.entities],
                relations=[self._to_relation_schema(relation) for relation in version.relations],
            )

    @staticmethod
    def _build_step_records(build_id: str) -> list[OntologyBuildStepORM]:
        return [
            OntologyBuildStepORM(
                id=f"{build_id}:{name}",
                build_id=build_id,
                name=name,
                status=OntologyStepStatus.pending.value,
                detail=None,
                started_at=None,
                finished_at=None,
            )
            for name in ONTOLOGY_BUILD_STEP_NAMES
        ]

    @staticmethod
    def _status_from_action(action: OntologyReviewAction) -> str:
        if action == OntologyReviewAction.approve:
            return OntologyReviewStatus.approved.value
        return OntologyReviewStatus.rejected.value

    @staticmethod
    def _get_step(session, build_id: str, name: str) -> OntologyBuildStepORM:
        step = session.scalar(
            select(OntologyBuildStepORM).where(
                OntologyBuildStepORM.build_id == build_id,
                OntologyBuildStepORM.name == name,
            )
        )
        if step is None:
            raise OntologyBuildError(
                f"Ontology build step '{name}' was not found for build '{build_id}'."
            )
        return step

    def _to_build_schemas(
        self,
        session,
        builds: list[OntologyBuildORM],
    ) -> list[OntologyBuildResponse]:
        build_ids = [build.id for build in builds]
        counts = self._load_build_counts(session, build_ids)
        steps_by_build = self._load_build_steps(session, build_ids)
        return [
            self._to_build_schema(
                build,
                entity_count=counts[build.id][0],
                relation_count=counts[build.id][1],
                pending_entity_count=counts[build.id][2],
                pending_relation_count=counts[build.id][3],
                steps=steps_by_build.get(build.id, []),
            )
            for build in builds
        ]

    def _load_build_counts(
        self,
        session,
        build_ids: list[str],
    ) -> dict[str, tuple[int, int, int, int]]:
        if not build_ids:
            return {}

        entity_counts = dict(
            session.execute(
                select(
                    OntologyCandidateEntityORM.build_id,
                    func.count(OntologyCandidateEntityORM.id),
                )
                .where(OntologyCandidateEntityORM.build_id.in_(build_ids))
                .group_by(OntologyCandidateEntityORM.build_id)
            ).all()
        )
        relation_counts = dict(
            session.execute(
                select(
                    OntologyCandidateRelationORM.build_id,
                    func.count(OntologyCandidateRelationORM.id),
                )
                .where(OntologyCandidateRelationORM.build_id.in_(build_ids))
                .group_by(OntologyCandidateRelationORM.build_id)
            ).all()
        )
        pending_entity_counts = dict(
            session.execute(
                select(
                    OntologyCandidateEntityORM.build_id,
                    func.count(OntologyCandidateEntityORM.id),
                )
                .where(
                    OntologyCandidateEntityORM.build_id.in_(build_ids),
                    OntologyCandidateEntityORM.status == OntologyReviewStatus.pending_review.value,
                )
                .group_by(OntologyCandidateEntityORM.build_id)
            ).all()
        )
        pending_relation_counts = dict(
            session.execute(
                select(
                    OntologyCandidateRelationORM.build_id,
                    func.count(OntologyCandidateRelationORM.id),
                )
                .where(
                    OntologyCandidateRelationORM.build_id.in_(build_ids),
                    OntologyCandidateRelationORM.status == OntologyReviewStatus.pending_review.value,
                )
                .group_by(OntologyCandidateRelationORM.build_id)
            ).all()
        )

        return {
            build_id: (
                int(entity_counts.get(build_id, 0)),
                int(relation_counts.get(build_id, 0)),
                int(pending_entity_counts.get(build_id, 0)),
                int(pending_relation_counts.get(build_id, 0)),
            )
            for build_id in build_ids
        }

    def _load_build_steps(
        self,
        session,
        build_ids: list[str],
    ) -> dict[str, list[OntologyBuildStepORM]]:
        if not build_ids:
            return {}
        steps_by_build: dict[str, list[OntologyBuildStepORM]] = defaultdict(list)
        steps = session.scalars(
            select(OntologyBuildStepORM).where(OntologyBuildStepORM.build_id.in_(build_ids))
        ).all()
        for step in steps:
            steps_by_build[step.build_id].append(step)
        for build_steps in steps_by_build.values():
            build_steps.sort(key=self._step_sort_key)
        return steps_by_build

    def _to_build_schema(
        self,
        build: OntologyBuildORM,
        *,
        entity_count: int,
        relation_count: int,
        pending_entity_count: int,
        pending_relation_count: int,
        steps: list[OntologyBuildStepORM],
    ) -> OntologyBuildResponse:
        return OntologyBuildResponse(
            id=build.id,
            document_id=build.document_id,
            workspace_id=build.workspace_id,
            status=build.status,
            domain=build.domain,
            created_at=build.created_at,
            started_at=build.started_at,
            finished_at=build.finished_at,
            updated_at=build.updated_at,
            error_message=build.error_message,
            published_version_id=build.published_version_id,
            entity_count=entity_count,
            relation_count=relation_count,
            pending_entity_count=pending_entity_count,
            pending_relation_count=pending_relation_count,
            entity_type_definitions=self._build_candidate_entity_type_definitions(build),
            relation_type_definitions=self._build_candidate_relation_type_definitions(build),
            steps=[self._to_step_schema(step) for step in steps],
        )

    @staticmethod
    def _to_step_schema(step: OntologyBuildStepORM) -> OntologyBuildStepResponse:
        return OntologyBuildStepResponse(
            id=step.id,
            name=step.name,
            status=step.status,
            detail=step.detail,
            started_at=step.started_at,
            finished_at=step.finished_at,
        )

    @staticmethod
    def _to_candidate_entity_schema(
        entity: OntologyCandidateEntityORM,
    ) -> OntologyCandidateEntityResponse:
        return OntologyCandidateEntityResponse(
            id=entity.id,
            build_id=entity.build_id,
            document_id=entity.document_id,
            workspace_id=entity.workspace_id,
            name=entity.name,
            canonical_name=entity.canonical_name,
            resolution_key=entity.resolution_key,
            entity_type=entity.entity_type,
            confidence=entity.confidence,
            status=entity.status,
            source_chunk_id=entity.source_chunk_id,
            evidence_text=entity.evidence_text,
            provenance=entity.provenance or {},
            aliases=entity.aliases or [],
            merged_into_entity_id=entity.merged_into_entity_id,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )

    @staticmethod
    def _to_candidate_relation_schema(
        relation: OntologyCandidateRelationORM,
    ) -> OntologyCandidateRelationResponse:
        return OntologyCandidateRelationResponse(
            id=relation.id,
            build_id=relation.build_id,
            document_id=relation.document_id,
            workspace_id=relation.workspace_id,
            source_entity_id=relation.source_entity_id,
            target_entity_id=relation.target_entity_id,
            source_name=relation.source_name,
            target_name=relation.target_name,
            relation_type=relation.relation_type,
            confidence=relation.confidence,
            status=relation.status,
            source_chunk_id=relation.source_chunk_id,
            evidence_text=relation.evidence_text,
            provenance=relation.provenance or {},
            created_at=relation.created_at,
            updated_at=relation.updated_at,
        )

    def _to_version_schema(self, version: OntologyVersionORM) -> OntologyVersionResponse:
        return OntologyVersionResponse(
            id=version.id,
            workspace_id=version.workspace_id,
            version_number=version.version_number,
            source_build_id=version.source_build_id,
            created_at=version.created_at,
            entity_type_count=len(version.entity_types),
            relation_type_count=len(version.relation_types),
            entity_count=len(version.entities),
            relation_count=len(version.relations),
        )

    @staticmethod
    def _to_entity_type_definition_schema(
        entity_type: OntologyEntityTypeDefinitionORM,
    ) -> OntologyEntityTypeDefinitionResponse:
        return OntologyEntityTypeDefinitionResponse(
            id=entity_type.id,
            version_id=entity_type.version_id,
            workspace_id=entity_type.workspace_id,
            name=entity_type.name,
            description=entity_type.description,
            attributes=entity_type.attributes or [],
            examples=entity_type.examples or [],
            created_at=entity_type.created_at,
        )

    @staticmethod
    def _to_relation_type_definition_schema(
        relation_type: OntologyRelationTypeDefinitionORM,
    ) -> OntologyRelationTypeDefinitionResponse:
        return OntologyRelationTypeDefinitionResponse(
            id=relation_type.id,
            version_id=relation_type.version_id,
            workspace_id=relation_type.workspace_id,
            name=relation_type.name,
            description=relation_type.description,
            attributes=relation_type.attributes or [],
            allowed_source_targets=relation_type.allowed_source_targets or [],
            created_at=relation_type.created_at,
        )

    @staticmethod
    def _to_entity_schema(entity: OntologyEntityORM) -> OntologyEntityResponse:
        return OntologyEntityResponse(
            id=entity.id,
            version_id=entity.version_id,
            workspace_id=entity.workspace_id,
            resolution_key=entity.resolution_key,
            name=entity.name,
            entity_type=entity.entity_type,
            aliases=entity.aliases or [],
            source_build_id=entity.source_build_id,
            source_document_id=entity.source_document_id,
            created_at=entity.created_at,
        )

    @staticmethod
    def _to_relation_schema(relation: OntologyRelationORM) -> OntologyRelationResponse:
        return OntologyRelationResponse(
            id=relation.id,
            version_id=relation.version_id,
            workspace_id=relation.workspace_id,
            source_entity_id=relation.source_entity_id,
            target_entity_id=relation.target_entity_id,
            relation_type=relation.relation_type,
            confidence=relation.confidence,
            source_build_id=relation.source_build_id,
            source_document_id=relation.source_document_id,
            evidence_text=relation.evidence_text,
            provenance=relation.provenance or {},
            created_at=relation.created_at,
        )

    @staticmethod
    def _step_sort_key(step: OntologyBuildStepORM) -> int:
        if step.name in ONTOLOGY_BUILD_STEP_NAMES:
            return ONTOLOGY_BUILD_STEP_NAMES.index(step.name)
        return len(ONTOLOGY_BUILD_STEP_NAMES)

    @staticmethod
    def _build_candidate_entity_type_definitions(
        build: OntologyBuildORM,
    ) -> list[OntologyEntityTypeDefinitionResponse]:
        entity_examples = OntologyService._collect_entity_examples(build.entities)
        return [
            OntologyEntityTypeDefinitionResponse(
                id=f"{build.id}:entity_type:{entity_type}",
                workspace_id=build.workspace_id,
                name=entity_type,
                description=f"Derived entity type for {entity_type}.",
                examples=examples[:3],
                created_at=build.updated_at,
            )
            for entity_type, examples in sorted(entity_examples.items())
        ]

    @staticmethod
    def _build_candidate_relation_type_definitions(
        build: OntologyBuildORM,
    ) -> list[OntologyRelationTypeDefinitionResponse]:
        allowed_pairs = OntologyService._collect_relation_allowed_pairs(
            entities=build.entities,
            relations=build.relations,
        )
        return [
            OntologyRelationTypeDefinitionResponse(
                id=f"{build.id}:relation_type:{relation_type}",
                workspace_id=build.workspace_id,
                name=relation_type,
                description=f"Derived relation type for {relation_type}.",
                allowed_source_targets=[
                    {
                        "source_entity_type": source_type,
                        "target_entity_type": target_type,
                    }
                    for source_type, target_type in sorted(pairs)
                ],
                created_at=build.updated_at,
            )
            for relation_type, pairs in sorted(allowed_pairs.items())
        ]

    @staticmethod
    def _build_entity_type_definitions(
        *,
        workspace_id: str,
        version_id: str,
        entities: list[OntologyCandidateEntityORM],
        created_at: datetime,
    ) -> list[OntologyEntityTypeDefinitionORM]:
        entity_examples = OntologyService._collect_entity_examples(entities)
        return [
            OntologyEntityTypeDefinitionORM(
                id=str(uuid4()),
                version_id=version_id,
                workspace_id=workspace_id,
                name=entity_type,
                description=f"Derived entity type for {entity_type}.",
                attributes=[],
                examples=examples[:3],
                created_at=created_at,
            )
            for entity_type, examples in sorted(entity_examples.items())
        ]

    @staticmethod
    def _build_relation_type_definitions(
        *,
        workspace_id: str,
        version_id: str,
        entities: list[OntologyCandidateEntityORM],
        relations: list[OntologyCandidateRelationORM],
        created_at: datetime,
    ) -> list[OntologyRelationTypeDefinitionORM]:
        allowed_pairs = OntologyService._collect_relation_allowed_pairs(
            entities=entities,
            relations=relations,
        )
        return [
            OntologyRelationTypeDefinitionORM(
                id=str(uuid4()),
                version_id=version_id,
                workspace_id=workspace_id,
                name=relation_type,
                description=f"Derived relation type for {relation_type}.",
                attributes=[],
                allowed_source_targets=[
                    {
                        "source_entity_type": source_type,
                        "target_entity_type": target_type,
                    }
                    for source_type, target_type in sorted(pairs)
                ],
                created_at=created_at,
            )
            for relation_type, pairs in sorted(allowed_pairs.items())
        ]

    @staticmethod
    def _collect_entity_examples(
        entities: list[OntologyCandidateEntityORM],
    ) -> dict[str, list[str]]:
        entity_examples: dict[str, list[str]] = defaultdict(list)
        for entity in entities:
            if entity.canonical_name not in entity_examples[entity.entity_type]:
                entity_examples[entity.entity_type].append(entity.canonical_name)
        return entity_examples

    @staticmethod
    def _collect_relation_allowed_pairs(
        *,
        entities: list[OntologyCandidateEntityORM],
        relations: list[OntologyCandidateRelationORM],
    ) -> dict[str, set[tuple[str, str]]]:
        entity_types_by_candidate_id = {
            entity.id: entity.entity_type for entity in entities if entity.id is not None
        }
        allowed_pairs: dict[str, set[tuple[str, str]]] = defaultdict(set)
        for relation in relations:
            source_type = entity_types_by_candidate_id.get(relation.source_entity_id or "")
            target_type = entity_types_by_candidate_id.get(relation.target_entity_id or "")
            if source_type and target_type:
                allowed_pairs[relation.relation_type].add((source_type, target_type))
        return allowed_pairs
