from collections import defaultdict
from datetime import datetime
from uuid import uuid4

from sqlalchemy import delete, desc, func, select, update
from sqlalchemy.orm import selectinload

from semantic_reasoning_agent.core.config import Settings
from semantic_reasoning_agent.persistence.database import DatabaseManager
from semantic_reasoning_agent.persistence.models.documents import DocumentChunkORM, DocumentORM
from semantic_reasoning_agent.persistence.models.ontology import (
    OntologyBuildORM,
    OntologyBuildStepORM,
    OntologyCandidateEntityORM,
    OntologyCandidateRelationORM,
    OntologyEntityORM,
    OntologyRelationORM,
    OntologyVersionORM,
)
from semantic_reasoning_agent.domain.ontology.models import ExtractedEntity, ExtractedRelation
from semantic_reasoning_agent.domain.ontology.models import OntologySourceChunk
from semantic_reasoning_agent.domain.ontology.pipeline_steps import ONTOLOGY_BUILD_STEP_NAMES
from semantic_reasoning_agent.ports.ontology_extractor import OntologyExtractorPort
from semantic_reasoning_agent.ports.graph_store import GraphStore, GraphStoreError, PublishedOntologySnapshot
from semantic_reasoning_agent.schemas.documents import DocumentStatus
from semantic_reasoning_agent.schemas.ontology import (
    KnowledgeGraphIngestResponse,
    KnowledgeGraphRelationPatch,
    OntologyBuildCreateRequest,
    OntologyBuildResponse,
    OntologyBuildStatus,
    OntologyEntityResponse,
    OntologyGraphResponse,
    OntologyPublishResponse,
    OntologyRelationResponse,
    OntologyReviewStatus,
    OntologyStepStatus,
    OntologyVersionResponse,
)
from semantic_reasoning_agent.services.ontology_errors import (
    OntologyBuildError,
    OntologyBuildNotFoundError,
    OntologyGraphError,
    OntologyPublishError,
    OntologyRelationNotFoundError,
    utc_now,
)
from semantic_reasoning_agent.services.ontology_mappers import (
    build_step_records,
    entity_to_response,
    relation_to_response,
    step_sort_key,
    step_to_response,
    version_to_response,
)
from semantic_reasoning_agent.services.ontology_architecture_service import (
    OntologyArchitectureService,
)
from semantic_reasoning_agent.workers.task_dispatcher import TaskDispatcher


class OntologyService:
    def __init__(
        self,
        settings: Settings,
        database_manager: DatabaseManager,
        task_dispatcher: TaskDispatcher,
        graph_store: GraphStore,
        ontology_extractor: OntologyExtractorPort,
        ontology_architecture_service: OntologyArchitectureService,
    ) -> None:
        self._settings = settings
        self._database_manager = database_manager
        self._task_dispatcher = task_dispatcher
        self._graph_store = graph_store
        self._ontology_extractor = ontology_extractor
        self._ontology_architecture_service = ontology_architecture_service

    def get_active_architecture_draft(self, workspace_id: str):
        return self._ontology_architecture_service.get_active_draft(workspace_id)

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
            session.add_all(build_step_records(build_id))

        if request.enqueue_processing:
            self._queue_build(build_id)
        return self.get_build(build_id)

    def get_build(self, build_id: str) -> OntologyBuildResponse:
        with self._database_manager.session() as session:
            build = session.scalar(
                select(OntologyBuildORM).where(OntologyBuildORM.id == build_id)
            )
            if build is None:
                raise OntologyBuildNotFoundError(f"Ontology build '{build_id}' was not found.")
            return self._to_build_schemas(session, [build])[0]

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
            if self._graph_store.is_enabled():
                self._graph_store.verify_connection()
                self._graph_store.sync_published_graph(snapshot)
        except GraphStoreError as exc:
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
        if self._graph_store.is_enabled():
            try:
                return self._graph_store.get_graph(resolved_workspace_id)
            except GraphStoreError as exc:
                raise OntologyGraphError(str(exc)) from exc
        return self._get_relational_graph(resolved_workspace_id)

    def approve_all_candidates(self, build_id: str) -> None:
        self._ensure_build_exists(build_id)
        timestamp = utc_now()
        with self._database_manager.session() as session:
            entities = session.scalars(
                select(OntologyCandidateEntityORM).where(
                    OntologyCandidateEntityORM.build_id == build_id
                )
            ).all()
            for entity in entities:
                entity.status = OntologyReviewStatus.approved.value
                entity.updated_at = timestamp
            relations = session.scalars(
                select(OntologyCandidateRelationORM).where(
                    OntologyCandidateRelationORM.build_id == build_id
                )
            ).all()
            for relation in relations:
                relation.status = OntologyReviewStatus.approved.value
                relation.updated_at = timestamp
            build = session.get(OntologyBuildORM, build_id)
            if build is not None:
                build.updated_at = timestamp

    def extract_sync_and_publish(
        self,
        document_id: str,
        workspace_id: str | None = None,
    ) -> OntologyPublishResponse:
        request = OntologyBuildCreateRequest(
            document_id=document_id,
            workspace_id=workspace_id,
            enqueue_processing=False,
        )
        build = self.create_build(request)
        self.process_build(build.id)
        self.approve_all_candidates(build.id)
        return self.publish_build(build.id)

    def ingest_documents_sync_publish(
        self,
        document_ids: list[str],
        workspace_id: str | None = None,
    ) -> KnowledgeGraphIngestResponse:
        if not document_ids:
            raise OntologyBuildError("At least one document_id is required.")
        resolved_workspace = workspace_id or self._settings.default_workspace_id
        build_ids: list[str] = []
        for doc_id in document_ids:
            request = OntologyBuildCreateRequest(
                document_id=doc_id,
                workspace_id=resolved_workspace,
                enqueue_processing=False,
            )
            build = self.create_build(request)
            self.process_build(build.id)
            self.approve_all_candidates(build.id)
            build_ids.append(build.id)
        publish = self.publish_merged_builds(resolved_workspace, build_ids)
        return KnowledgeGraphIngestResponse(
            workspace_id=resolved_workspace,
            document_ids=document_ids,
            build_ids=build_ids,
            publish=publish,
        )

    def publish_merged_builds(
        self,
        workspace_id: str,
        build_ids: list[str],
    ) -> OntologyPublishResponse:
        build_ids = list(dict.fromkeys(build_ids))
        if not build_ids:
            raise OntologyPublishError("No ontology builds to publish.")
        if len(build_ids) == 1:
            return self.publish_build(build_ids[0])
        snapshot = self._prepare_merged_snapshot(workspace_id, build_ids)
        try:
            if self._graph_store.is_enabled():
                self._graph_store.verify_connection()
                self._graph_store.sync_published_graph(snapshot)
        except GraphStoreError as exc:
            raise OntologyPublishError(str(exc)) from exc
        with self._database_manager.session() as session:
            for bid in build_ids:
                build = session.get(OntologyBuildORM, bid)
                if build is None:
                    continue
                build.status = OntologyBuildStatus.published.value
                build.published_version_id = snapshot.version.id
                build.updated_at = utc_now()
        return OntologyPublishResponse(
            build=self.get_build(build_ids[0]),
            version=snapshot.version,
        )

    def _prepare_merged_snapshot(
        self,
        workspace_id: str,
        build_ids: list[str],
    ) -> PublishedOntologySnapshot:
        version_timestamp = utc_now()
        with self._database_manager.session() as session:
            builds = session.scalars(
                select(OntologyBuildORM)
                .options(
                    selectinload(OntologyBuildORM.entities),
                    selectinload(OntologyBuildORM.relations),
                )
                .where(OntologyBuildORM.id.in_(build_ids))
            ).all()
            if len(builds) != len(build_ids):
                raise OntologyBuildNotFoundError("One or more ontology builds were not found.")
            build_by_id = {b.id: b for b in builds}
            ordered = [build_by_id[bid] for bid in build_ids]
            for build in ordered:
                if build.workspace_id != workspace_id:
                    raise OntologyPublishError(
                        f"Build '{build.id}' belongs to a different workspace than '{workspace_id}'."
                    )
                if build.status != OntologyBuildStatus.completed.value:
                    raise OntologyPublishError(
                        f"Ontology build '{build.id}' must complete before it can be merged."
                    )

            merged_by_key: dict[str, OntologyCandidateEntityORM] = {}
            for build in ordered:
                for entity in build.entities:
                    if entity.status != OntologyReviewStatus.approved.value:
                        continue
                    if entity.merged_into_entity_id is not None:
                        continue
                    if entity.resolution_key not in merged_by_key:
                        merged_by_key[entity.resolution_key] = entity

            if not merged_by_key:
                raise OntologyPublishError("Merged publish has no approved entities.")

            published_entity_by_key: dict[str, str] = {
                key: str(uuid4()) for key in merged_by_key
            }

            latest = session.scalar(
                select(OntologyVersionORM)
                .where(OntologyVersionORM.workspace_id == workspace_id)
                .order_by(desc(OntologyVersionORM.version_number))
            )
            next_version_number = 1 if latest is None else latest.version_number + 1

            session.execute(
                update(OntologyBuildORM)
                .where(OntologyBuildORM.workspace_id == workspace_id)
                .values(published_version_id=None)
            )
            for row in session.scalars(
                select(OntologyVersionORM).where(OntologyVersionORM.workspace_id == workspace_id)
            ).all():
                session.delete(row)

            version_id = str(uuid4())
            version = OntologyVersionORM(
                id=version_id,
                workspace_id=workspace_id,
                version_number=next_version_number,
                source_build_id=build_ids[0],
                created_at=version_timestamp,
            )
            session.add(version)

            version_entities: list[OntologyEntityResponse] = []
            for key, cand in merged_by_key.items():
                peid = published_entity_by_key[key]
                row = OntologyEntityORM(
                    id=peid,
                    version_id=version_id,
                    workspace_id=workspace_id,
                    resolution_key=cand.resolution_key,
                    name=cand.canonical_name,
                    entity_type=cand.entity_type,
                    aliases=sorted(set(cand.aliases or [])),
                    source_build_id=cand.build_id,
                    source_document_id=cand.document_id,
                    created_at=version_timestamp,
                )
                session.add(row)
                version_entities.append(entity_to_response(row))

            seen_rel: set[tuple[str, str, str]] = set()
            version_relations: list[OntologyRelationResponse] = []
            for build in ordered:
                for relation in build.relations:
                    if relation.status != OntologyReviewStatus.approved.value:
                        continue
                    src = session.get(OntologyCandidateEntityORM, relation.source_entity_id)
                    tgt = session.get(OntologyCandidateEntityORM, relation.target_entity_id)
                    if src is None or tgt is None:
                        continue
                    sk, tk = src.resolution_key, tgt.resolution_key
                    if sk not in published_entity_by_key or tk not in published_entity_by_key:
                        continue
                    dedupe = (sk, tk, relation.relation_type)
                    if dedupe in seen_rel:
                        continue
                    seen_rel.add(dedupe)
                    pr = OntologyRelationORM(
                        id=str(uuid4()),
                        version_id=version_id,
                        workspace_id=workspace_id,
                        source_entity_id=published_entity_by_key[sk],
                        target_entity_id=published_entity_by_key[tk],
                        relation_type=relation.relation_type,
                        confidence=relation.confidence,
                        source_build_id=relation.build_id,
                        source_document_id=relation.document_id,
                        evidence_text=relation.evidence_text,
                        provenance=relation.provenance or {},
                        created_at=version_timestamp,
                    )
                    session.add(pr)
                    version_relations.append(relation_to_response(pr))

            version_schema = OntologyVersionResponse(
                id=version_id,
                workspace_id=workspace_id,
                version_number=next_version_number,
                source_build_id=build_ids[0],
                created_at=version_timestamp,
                entity_count=len(version_entities),
                relation_count=len(version_relations),
            )
            return PublishedOntologySnapshot(
                workspace_id=workspace_id,
                version=version_schema,
                entities=version_entities,
                relations=version_relations,
            )

    def _build_published_snapshot(self, version_id: str) -> PublishedOntologySnapshot:
        with self._database_manager.session() as session:
            version = session.scalar(
                select(OntologyVersionORM)
                .options(
                    selectinload(OntologyVersionORM.entities),
                    selectinload(OntologyVersionORM.relations),
                )
                .where(OntologyVersionORM.id == version_id)
            )
            if version is None:
                raise OntologyGraphError(f"Ontology version '{version_id}' was not found.")
            return PublishedOntologySnapshot(
                workspace_id=version.workspace_id,
                version=version_to_response(version),
                entities=[entity_to_response(e) for e in version.entities],
                relations=[relation_to_response(r) for r in version.relations],
            )

    def patch_published_relation(
        self,
        relation_id: str,
        patch: KnowledgeGraphRelationPatch,
    ) -> OntologyRelationResponse:
        with self._database_manager.session() as session:
            relation = session.get(OntologyRelationORM, relation_id)
            if relation is None:
                raise OntologyRelationNotFoundError(
                    f"Published ontology relation '{relation_id}' was not found."
                )
            if patch.relation_type is not None:
                relation.relation_type = patch.relation_type
            if patch.confidence is not None:
                relation.confidence = patch.confidence
            if patch.evidence_text is not None:
                relation.evidence_text = patch.evidence_text
            version_id = relation.version_id

        snapshot = self._build_published_snapshot(version_id)
        if self._graph_store.is_enabled():
            try:
                self._graph_store.verify_connection()
                self._graph_store.sync_published_graph(snapshot)
            except GraphStoreError as exc:
                raise OntologyGraphError(str(exc)) from exc

        with self._database_manager.session() as session:
            updated = session.get(OntologyRelationORM, relation_id)
            if updated is None:
                raise OntologyRelationNotFoundError(
                    f"Published ontology relation '{relation_id}' was not found."
                )
            return relation_to_response(updated)

    def delete_workspace_graph(self, workspace_id: str | None = None) -> None:
        resolved = workspace_id or self._settings.default_workspace_id
        with self._database_manager.session() as session:
            for row in session.scalars(
                select(OntologyVersionORM).where(OntologyVersionORM.workspace_id == resolved)
            ).all():
                session.delete(row)
            session.execute(
                update(OntologyBuildORM)
                .where(OntologyBuildORM.workspace_id == resolved)
                .values(published_version_id=None)
            )
        if self._graph_store.is_enabled():
            try:
                self._graph_store.verify_connection()
                self._graph_store.delete_workspace(resolved)
            except GraphStoreError as exc:
                raise OntologyGraphError(str(exc)) from exc

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
            architecture_draft = self._ontology_architecture_service.ensure_active_draft(
                workspace_id=build.workspace_id,
                source_document_ids=[build.document_id],
                source_build_id=build.id,
                chunk_samples=[
                    (chunk.chunk_id, build.document_id, chunk.text[:1000])
                    for chunk in chunks[:8]
                ],
            )
            self._mark_step_running(build_id, "classify_document_domain")
            domain = architecture_draft.domain or self._ontology_extractor.classify_document_domain(chunks)
            self._mark_step_completed(
                build_id,
                "classify_document_domain",
                detail=(
                    f"Resolved document domain '{domain}' using ontology architecture "
                    f"draft '{architecture_draft.draft_id}'."
                ),
            )
            self._update_build_state(
                build_id,
                status=OntologyBuildStatus.running.value,
                domain=domain,
                architecture_draft_id=architecture_draft.draft_id,
            )

            self._mark_step_running(build_id, "extract_entities")
            extraction = self._ontology_extractor.extract_ontology_candidates(
                chunks,
                workspace_id=build.workspace_id,
                architecture_draft=architecture_draft,
            )
            resolved_domain = extraction.domain if extraction.domain and extraction.domain != "pending" else domain
            if resolved_domain != domain:
                self._update_build_state(
                    build_id,
                    status=OntologyBuildStatus.running.value,
                    domain=resolved_domain,
                    architecture_draft_id=architecture_draft.draft_id,
                )
                domain = resolved_domain
            entity_id_map = self._replace_candidate_entities(
                build,
                extraction.entities,
                extraction_run_id=extraction_run_id,
                architecture_draft_id=architecture_draft.draft_id,
            )
            self._mark_step_completed(
                build_id,
                "extract_entities",
                detail=(
                    f"Extracted {len(extraction.entities)} candidate entities "
                    f"using architecture draft '{architecture_draft.draft_id}'."
                ),
            )

            self._mark_step_running(build_id, "extract_relations")
            self._replace_candidate_relations(
                build,
                extraction.relations,
                entity_id_map,
                extraction_run_id=extraction_run_id,
                architecture_draft_id=architecture_draft.draft_id,
            )
            self._mark_step_completed(
                build_id,
                "extract_relations",
                detail=(
                    f"Extracted {len(extraction.relations)} candidate relations "
                    f"using architecture draft '{architecture_draft.draft_id}'."
                ),
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
            if self._graph_store.is_enabled():
                self._graph_store.verify_connection()
                sync_detail = "Neo4j connection verified; publish will sync the approved graph snapshot."
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
            build.architecture_draft_id = None
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
        architecture_draft_id: str | None = None,
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
            if architecture_draft_id is not None:
                build.architecture_draft_id = architecture_draft_id
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
        architecture_draft_id: str | None,
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
                            "architecture_draft_id": architecture_draft_id,
                        },
                        aliases=sorted(entity.aliases),
                        architecture_draft_id=architecture_draft_id,
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
        architecture_draft_id: str | None,
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
                            "architecture_draft_id": architecture_draft_id,
                        },
                        architecture_draft_id=architecture_draft_id,
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
                        selectinload(OntologyVersionORM.relations),
                    )
                    .where(OntologyVersionORM.id == build.published_version_id)
                )
            if existing_version is not None:
                return PublishedOntologySnapshot(
                    workspace_id=build.workspace_id,
                    version=version_to_response(existing_version),
                    entities=[entity_to_response(entity) for entity in existing_version.entities],
                    relations=[relation_to_response(relation) for relation in existing_version.relations],
                )

            stale_versions = session.scalars(
                select(OntologyVersionORM)
                .options(
                    selectinload(OntologyVersionORM.entities),
                    selectinload(OntologyVersionORM.relations),
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
                version_entities.append(entity_to_response(published_entity))

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
                version_relations.append(relation_to_response(published_relation))

            version_schema = OntologyVersionResponse(
                id=version_id,
                workspace_id=build.workspace_id,
                version_number=next_version_number,
                source_build_id=build.id,
                created_at=version_timestamp,
                entity_count=len(version_entities),
                relation_count=len(version_relations),
            )
            return PublishedOntologySnapshot(
                workspace_id=build.workspace_id,
                version=version_schema,
                entities=version_entities,
                relations=version_relations,
            )

    def _get_relational_graph(self, workspace_id: str) -> OntologyGraphResponse:
        with self._database_manager.session() as session:
            version = session.scalar(
                select(OntologyVersionORM)
                .options(
                    selectinload(OntologyVersionORM.entities),
                    selectinload(OntologyVersionORM.relations),
                )
                .where(OntologyVersionORM.workspace_id == workspace_id)
                .order_by(desc(OntologyVersionORM.version_number))
            )
            if version is None:
                return OntologyGraphResponse(workspace_id=workspace_id)
            return OntologyGraphResponse(
                workspace_id=workspace_id,
                version=version_to_response(version),
                entities=[entity_to_response(entity) for entity in version.entities],
                relations=[relation_to_response(relation) for relation in version.relations],
            )

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
            build_steps.sort(key=step_sort_key)
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
            steps=[step_to_response(step) for step in steps],
        )
