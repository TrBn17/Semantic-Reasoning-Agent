from datetime import datetime, timezone
from collections import defaultdict
from copy import deepcopy
from dataclasses import asdict, is_dataclass
from uuid import uuid4

from sqlalchemy import delete, desc, select
from sqlalchemy.orm import selectinload

from semantic_reasoning_agent.core.config import Settings
from semantic_reasoning_agent.domain.contracts.published_ontology_snapshot import PublishedOntologySnapshot
from semantic_reasoning_agent.infrastructure.graphiti.graphiti_gateway import GraphitiGateway
from semantic_reasoning_agent.infrastructure.storage import build_object_store
from semantic_reasoning_agent.persistence.database import DatabaseManager
from semantic_reasoning_agent.persistence.models import (
    DocumentArtifactORM,
    DocumentChunkORM,
    DocumentORM,
    OntologyBuildORM,
    OntologyBuildStepORM,
    OntologyEntityORM,
    OntologyEntityFactORM,
    OntologyEntityTypeDefinitionORM,
    OntologyGraphDraftORM,
    OntologyRelationORM,
    OntologyRelationFactORM,
    OntologyRelationTypeDefinitionORM,
    OntologyVersionORM,
)
from semantic_reasoning_agent.domain.ontology.models import OntologyDocument
from semantic_reasoning_agent.domain.ontology.pipeline_steps import ONTOLOGY_BUILD_STEP_NAMES
from semantic_reasoning_agent.ports.object_store import ObjectStorePort
from semantic_reasoning_agent.ports.ontology_extractor import OntologyExtractorPort
from semantic_reasoning_agent.schemas.documents import DocumentStatus
from semantic_reasoning_agent.schemas.ontology import (
    OntologyBuildCreateRequest,
    OntologyBuildResponse,
    OntologyBuildStatus,
    OntologyBuildStepResponse,
    OntologyEntityTypeDefinitionResponse,
    OntologyEntityResponse,
    OntologyEntityTypeDefinitionUpdateRequest,
    OntologyDraftPublishRequest,
    OntologyGraphResponse,
    OntologyGraphDraftResponse,
    OntologyGraphDraftNodeRequest,
    OntologyGraphDraftNodeUpdateRequest,
    OntologyGraphDraftRelationRequest,
    OntologyGraphDraftRelationUpdateRequest,
    OntologyGraphDraftSummaryResponse,
    OntologyMergeMode,
    OntologyRelationTypeDefinitionResponse,
    OntologyRelationTypeDefinitionUpdateRequest,
    OntologyPublishPreviewResponse,
    OntologyPublishResponse,
    OntologyRelationResponse,
    OntologyStepStatus,
    OntologyVersionResponse,
)
from semantic_reasoning_agent.services.ontology_graph_publisher import (
    GraphitiDocumentChunk,
    OntologyGraphPublisher,
    OntologyGraphPublisherError,
)
from semantic_reasoning_agent.workers.task_dispatcher import TaskDispatcher


def utc_now() -> datetime:
    return datetime.now(timezone.utc)

class OntologyBuildNotFoundError(ValueError):
    """Raised when an ontology build id does not exist."""


class OntologyBuildError(ValueError):
    """Raised when an ontology build cannot be created or processed."""


class OntologyPublishError(ValueError):
    """Raised when an ontology build cannot be published."""


class OntologyGraphError(ValueError):
    """Raised when the published graph cannot be read."""


class OntologyDraftError(ValueError):
    """Raised when ontology draft edits are invalid."""


class OntologyService:
    def __init__(
        self,
        settings: Settings,
        database_manager: DatabaseManager,
        task_dispatcher: TaskDispatcher,
        graphiti_gateway: GraphitiGateway,
        ontology_extractor: OntologyExtractorPort,
        object_store: ObjectStorePort | None = None,
    ) -> None:
        self._settings = settings
        self._database_manager = database_manager
        self._task_dispatcher = task_dispatcher
        self._graphiti_gateway = graphiti_gateway
        self._graph_publisher = OntologyGraphPublisher(graphiti_gateway)
        self._ontology_extractor = ontology_extractor
        self._object_store = object_store or build_object_store(settings)

    def create_build(self, request: OntologyBuildCreateRequest) -> OntologyBuildResponse:
        with self._database_manager.session() as session:
            document = session.get(DocumentORM, request.document_id)
            if document is None:
                raise OntologyBuildError(f"Document '{request.document_id}' was not found.")
            if document.status != DocumentStatus.indexed.value:
                raise OntologyBuildError(
                    f"Document '{request.document_id}' must be indexed before ontology extraction starts."
                )
            if not request.extraction_provider or not request.extraction_model:
                raise OntologyBuildError(
                    "Ontology build requires explicit extraction_provider and extraction_model."
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
                    ontology_title=None,
                    ontology_summary=None,
                    merge_mode=request.merge_mode.value,
                    extraction_provider=request.extraction_provider,
                    extraction_model=request.extraction_model,
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

    def delete_build(self, build_id: str) -> None:
        with self._database_manager.session() as session:
            build = session.get(OntologyBuildORM, build_id)
            if build is None:
                raise OntologyBuildNotFoundError(f"Ontology build '{build_id}' was not found.")
            if build.status != OntologyBuildStatus.failed.value:
                raise OntologyBuildError("Only failed ontology builds can be deleted.")
            session.delete(build)

    def get_graph(self, workspace_id: str | None = None) -> OntologyGraphResponse:
        resolved_workspace_id = workspace_id or self._settings.default_workspace_id
        return self._get_relational_graph(resolved_workspace_id)

    def get_graph_draft(self, workspace_id: str | None = None) -> OntologyGraphDraftResponse:
        resolved_workspace_id = workspace_id or self._settings.default_workspace_id
        snapshot, draft_summary = self._build_workspace_snapshot(
            workspace_id=resolved_workspace_id,
            include_draft=True,
        )
        return OntologyGraphDraftResponse(
            workspace_id=resolved_workspace_id,
            version=snapshot.version,
            ontology_title=snapshot.version.ontology_title if snapshot.version else None,
            ontology_summary=snapshot.version.ontology_summary if snapshot.version else None,
            has_changes=draft_summary.has_changes,
            entity_type_definitions=snapshot.entity_type_definitions,
            relation_type_definitions=snapshot.relation_type_definitions,
            entities=snapshot.entities,
            relations=snapshot.relations,
            draft_summary=draft_summary,
        )

    def create_draft_node(
        self,
        request: OntologyGraphDraftNodeRequest,
        *,
        workspace_id: str | None = None,
    ) -> OntologyGraphDraftResponse:
        resolved_workspace_id = workspace_id or self._settings.default_workspace_id
        node_id = request.id or f"draft-node-{uuid4()}"
        patch = {
            "id": node_id,
            "op": "upsert",
            "name": request.name,
            "entity_type": request.entity_type,
            "resolution_key": request.resolution_key or self._slugify(request.name),
            "aliases": sorted(set(request.aliases or [])),
            "query_rules": self._serialize_query_rules(request.query_rules),
            "source_document_id": request.source_document_id or "draft",
            "source_build_id": request.source_build_id or "draft",
        }
        self._upsert_draft_patch(resolved_workspace_id, "node_patches", node_id, patch)
        return self.get_graph_draft(resolved_workspace_id)

    def update_draft_node(
        self,
        node_id: str,
        request: OntologyGraphDraftNodeUpdateRequest,
        *,
        workspace_id: str | None = None,
    ) -> OntologyGraphDraftResponse:
        resolved_workspace_id = workspace_id or self._settings.default_workspace_id
        patch = self._existing_node_patch(resolved_workspace_id, node_id)
        payload = request.model_dump(exclude_unset=True)
        patch = {**patch, **payload, "id": node_id, "op": "upsert"}
        if "aliases" in payload and payload["aliases"] is not None:
            patch["aliases"] = sorted(set(payload["aliases"]))
        if not patch.get("resolution_key") and patch.get("name"):
            patch["resolution_key"] = self._slugify(str(patch["name"]))
        self._upsert_draft_patch(resolved_workspace_id, "node_patches", node_id, patch)
        return self.get_graph_draft(resolved_workspace_id)

    def delete_draft_node(self, node_id: str, *, workspace_id: str | None = None) -> OntologyGraphDraftResponse:
        resolved_workspace_id = workspace_id or self._settings.default_workspace_id
        self._upsert_draft_patch(resolved_workspace_id, "node_patches", node_id, {"id": node_id, "op": "delete"})
        self._delete_relations_for_missing_node(resolved_workspace_id, node_id)
        return self.get_graph_draft(resolved_workspace_id)

    def create_draft_relation(
        self,
        request: OntologyGraphDraftRelationRequest,
        *,
        workspace_id: str | None = None,
    ) -> OntologyGraphDraftResponse:
        resolved_workspace_id = workspace_id or self._settings.default_workspace_id
        relation_id = request.id or f"draft-relation-{uuid4()}"
        self._ensure_relation_endpoints_exist(
            resolved_workspace_id,
            request.source_entity_id,
            request.target_entity_id,
        )
        patch = {
            "id": relation_id,
            "op": "upsert",
            "source_entity_id": request.source_entity_id,
            "target_entity_id": request.target_entity_id,
            "relation_type": request.relation_type,
            "confidence": float(request.confidence),
            "evidence_text": request.evidence_text,
            "query_rules": self._serialize_query_rules(request.query_rules),
            "source_document_id": request.source_document_id or "draft",
            "source_build_id": request.source_build_id or "draft",
            "provenance": {"source": "draft_editor"},
        }
        self._upsert_draft_patch(resolved_workspace_id, "relation_patches", relation_id, patch)
        return self.get_graph_draft(resolved_workspace_id)

    def update_draft_relation(
        self,
        relation_id: str,
        request: OntologyGraphDraftRelationUpdateRequest,
        *,
        workspace_id: str | None = None,
    ) -> OntologyGraphDraftResponse:
        resolved_workspace_id = workspace_id or self._settings.default_workspace_id
        patch = self._existing_relation_patch(resolved_workspace_id, relation_id)
        payload = request.model_dump(exclude_unset=True)
        merged = {**patch, **payload, "id": relation_id, "op": "upsert"}
        self._ensure_relation_endpoints_exist(
            resolved_workspace_id,
            str(merged["source_entity_id"]),
            str(merged["target_entity_id"]),
        )
        self._upsert_draft_patch(resolved_workspace_id, "relation_patches", relation_id, merged)
        return self.get_graph_draft(resolved_workspace_id)

    def delete_draft_relation(
        self,
        relation_id: str,
        *,
        workspace_id: str | None = None,
    ) -> OntologyGraphDraftResponse:
        resolved_workspace_id = workspace_id or self._settings.default_workspace_id
        self._upsert_draft_patch(
            resolved_workspace_id,
            "relation_patches",
            relation_id,
            {"id": relation_id, "op": "delete"},
        )
        return self.get_graph_draft(resolved_workspace_id)

    def update_draft_entity_type(
        self,
        type_id: str,
        request: OntologyEntityTypeDefinitionUpdateRequest,
        *,
        workspace_id: str | None = None,
    ) -> OntologyGraphDraftResponse:
        resolved_workspace_id = workspace_id or self._settings.default_workspace_id
        payload = request.model_dump(exclude_unset=True)
        patch = {"id": type_id, "op": "delete" if payload.get("deleted") else "upsert", **payload}
        self._upsert_draft_patch(resolved_workspace_id, "entity_type_patches", type_id, patch)
        return self.get_graph_draft(resolved_workspace_id)

    def update_draft_relation_type(
        self,
        type_id: str,
        request: OntologyRelationTypeDefinitionUpdateRequest,
        *,
        workspace_id: str | None = None,
    ) -> OntologyGraphDraftResponse:
        resolved_workspace_id = workspace_id or self._settings.default_workspace_id
        payload = request.model_dump(exclude_unset=True)
        patch = {"id": type_id, "op": "delete" if payload.get("deleted") else "upsert", **payload}
        self._upsert_draft_patch(resolved_workspace_id, "relation_type_patches", type_id, patch)
        return self.get_graph_draft(resolved_workspace_id)

    def reset_graph_draft(self, workspace_id: str | None = None) -> OntologyGraphDraftResponse:
        resolved_workspace_id = workspace_id or self._settings.default_workspace_id
        with self._database_manager.session() as session:
            draft = session.get(OntologyGraphDraftORM, resolved_workspace_id)
            if draft is not None:
                session.delete(draft)
        return self.get_graph_draft(resolved_workspace_id)

    def publish_graph_draft(self, request: OntologyDraftPublishRequest) -> OntologyPublishResponse:
        workspace_id = request.workspace_id or self._settings.default_workspace_id
        snapshot, _ = self._build_publish_snapshot(build_id=request.build_id, workspace_id=workspace_id)
        graphiti_chunks = self._load_graphiti_chunks_for_snapshot(snapshot)
        try:
            self._graph_publisher.publish(snapshot, document_chunks=graphiti_chunks)
        except OntologyGraphPublisherError as exc:
            raise OntologyPublishError(str(exc)) from exc
        if request.build_id:
            with self._database_manager.session() as session:
                build = session.get(OntologyBuildORM, request.build_id)
                if build is not None:
                    build.status = OntologyBuildStatus.published.value
                    build.published_version_id = snapshot.version.id
                    build.updated_at = utc_now()
        self._clear_draft(workspace_id)
        build_response = self.get_build(request.build_id) if request.build_id else self._empty_build_for_publish(workspace_id)
        return OntologyPublishResponse(build=build_response, version=snapshot.version)

    def process_build(self, build_id: str) -> None:
        build = self._get_build_record(build_id)
        document = self._get_document_markdown(build.document_id)
        if not document.markdown.strip():
            raise OntologyBuildError(
                f"Document '{build.document_id}' does not have markdown content for ontology extraction."
            )

        self._reset_build(build_id)
        self._mark_build_running(build_id)
        try:
            self._mark_step_running(build_id, "classify_document_domain")
            preliminary_domain = self._ontology_extractor.classify_document_domain(document)
            classify_detail = (
                "Document domain classification is deferred to ontology extraction."
                if preliminary_domain == "pending"
                else f"Detected document domain '{preliminary_domain}'."
            )
            self._mark_step_completed(
                build_id,
                "classify_document_domain",
                detail=classify_detail,
            )
            self._update_build_state(
                build_id,
                status=OntologyBuildStatus.running.value,
                domain=None if preliminary_domain == "pending" else preliminary_domain,
            )

            self._mark_step_running(build_id, "extract_entities")
            extraction = self._ontology_extractor.extract_ontology_candidates(
                document,
                workspace_id=build.workspace_id,
                provider=build.extraction_provider,
                model=build.extraction_model,
            )
            resolved_domain = extraction.domain or preliminary_domain
            if (
                resolved_domain in {"unavailable", "unconfigured", "disabled"}
                and not extraction.entities
                and not extraction.relations
            ):
                raise OntologyBuildError(
                    "Ontology extraction model is unavailable for the selected provider/model. "
                    "Verify provider settings, credentials, and runtime readiness, then retry."
                )
            if resolved_domain and resolved_domain != "pending":
                self._update_build_state(
                    build_id,
                    status=OntologyBuildStatus.running.value,
                    domain=resolved_domain,
                )
            narrative = self._ontology_extractor.summarize_ontology(
                document,
                workspace_id=build.workspace_id,
                provider=build.extraction_provider,
                model=build.extraction_model,
                domain=resolved_domain,
            )
            self._update_build_metadata(
                build_id,
                ontology_title=narrative.title,
                ontology_summary=narrative.summary,
            )
            self._mark_step_completed(
                build_id,
                "extract_entities",
                detail=f"Extracted {len(extraction.entities)} candidate entities.",
                metadata={
                    "safe_trace": {
                        **(extraction.trace or {}),
                        "domain": resolved_domain,
                        "chunk_count": len((extraction.trace or {}).get("chunks", [])),
                        "errors": (extraction.trace or {}).get("errors", []),
                        "entity_count": len(extraction.entities),
                    }
                },
            )

            self._mark_step_running(build_id, "extract_relations")
            self._mark_step_completed(
                build_id,
                "extract_relations",
                detail=f"Extracted {len(extraction.relations)} candidate relations.",
                metadata={
                    "safe_trace": {
                        **(extraction.trace or {}),
                        "domain": resolved_domain,
                        "chunk_count": len((extraction.trace or {}).get("chunks", [])),
                        "errors": (extraction.trace or {}).get("errors", []),
                        "relation_count": len(extraction.relations),
                    }
                },
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
                    "Candidate persistence is disabled. "
                    f"Extraction finished with {len(extraction.entities)} entities and {len(extraction.relations)} relations."
                ),
            )

            self._mark_step_running(build_id, "sync_neo4j")
            sync_detail = (
                "Graph runtime is disabled. Build stores relational candidates only; graph sync happens on publish."
            )
            if self._graph_publisher.is_enabled():
                self._graph_publisher.publish()
                sync_detail = (
                    "Graphiti/Neo4j is enabled and indices were prepared. "
                    "Ontology nodes/edges are synced only when the build is published."
                )
            self._mark_step_completed(
                build_id,
                "sync_neo4j",
                detail=sync_detail,
            )

            self._update_build_state(
                build_id,
                status=OntologyBuildStatus.completed.value,
                domain=None if resolved_domain == "pending" else resolved_domain,
                finished_at=utc_now(),
                error_message=None,
            )
        except Exception as exc:
            error_message = self._format_processing_error(exc)
            self._mark_failed(build_id, self._active_step_name(build_id), error_message)
            raise OntologyBuildError(error_message) from exc

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
                ontology_title=build.ontology_title,
                ontology_summary=build.ontology_summary,
                merge_mode=build.merge_mode,
                extraction_provider=build.extraction_provider,
                extraction_model=build.extraction_model,
                created_at=build.created_at,
                started_at=build.started_at,
                finished_at=build.finished_at,
                updated_at=build.updated_at,
                error_message=build.error_message,
                published_version_id=build.published_version_id,
            )

    def _get_document_markdown(self, document_id: str) -> OntologyDocument:
        with self._database_manager.session() as session:
            artifact = session.scalar(
                select(DocumentArtifactORM)
                .where(
                    DocumentArtifactORM.document_id == document_id,
                    DocumentArtifactORM.artifact_type == "markdown",
                )
                .order_by(desc(DocumentArtifactORM.created_at))
            )
        if artifact is None:
            return OntologyDocument(document_id=document_id, markdown="")
        markdown_bytes = self._object_store.get_document_binary(document_id, artifact.object_key)
        if markdown_bytes:
            markdown = markdown_bytes.decode("utf-8")
        else:
            inline_text = (artifact.metadata_json or {}).get("inline_text")
            markdown = inline_text if isinstance(inline_text, str) else ""
        markdown = markdown[: self._settings.ontology_markdown_char_limit]
        return OntologyDocument(document_id=document_id, markdown=markdown)

    def _reset_build(self, build_id: str) -> None:
        with self._database_manager.session() as session:
            build = session.get(OntologyBuildORM, build_id)
            if build is None:
                raise OntologyBuildNotFoundError(f"Ontology build '{build_id}' was not found.")
            build.status = OntologyBuildStatus.pending.value
            build.error_message = None
            build.domain = None
            build.ontology_title = None
            build.ontology_summary = None
            build.started_at = None
            build.finished_at = None
            build.updated_at = utc_now()
            for step in session.scalars(
                select(OntologyBuildStepORM).where(OntologyBuildStepORM.build_id == build_id)
            ).all():
                step.status = OntologyStepStatus.pending.value
                step.detail = None
                step.metadata_json = {}
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

    def _update_build_metadata(
        self,
        build_id: str,
        *,
        ontology_title: str | None = None,
        ontology_summary: str | None = None,
    ) -> None:
        with self._database_manager.session() as session:
            build = session.get(OntologyBuildORM, build_id)
            if build is None:
                raise OntologyBuildNotFoundError(f"Ontology build '{build_id}' was not found.")
            if ontology_title is not None:
                build.ontology_title = ontology_title
            if ontology_summary is not None:
                build.ontology_summary = ontology_summary
            build.updated_at = utc_now()

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
                        metadata_json={},
                        started_at=None,
                        finished_at=None,
                    )
                    session.add(step)
                if name == failed_step:
                    failure_reached = True
                    step.status = OntologyStepStatus.failed.value
                    step.detail = error_message
                    step.metadata_json = {}
                    step.started_at = timestamp
                    step.finished_at = timestamp
                elif failure_reached:
                    step.status = OntologyStepStatus.pending.value
                    step.detail = None
                    step.metadata_json = {}
                    step.started_at = None
                    step.finished_at = None
                else:
                    step.status = OntologyStepStatus.completed.value
                    step.metadata_json = {}
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
            step.metadata_json = {}

    def _mark_step_completed(
        self,
        build_id: str,
        name: str,
        detail: str | None = None,
        metadata: dict[str, object] | None = None,
    ) -> None:
        with self._database_manager.session() as session:
            step = self._get_step(session, build_id, name)
            now = utc_now()
            step.status = OntologyStepStatus.completed.value
            if step.started_at is None:
                step.started_at = now
            step.finished_at = now
            step.detail = detail
            step.metadata_json = metadata or {}

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

    def _format_processing_error(self, exc: Exception) -> str:
        status_code = getattr(exc, "status_code", None)
        if status_code == 429:
            provider_message = self._provider_error_message(exc)
            if provider_message:
                return (
                    "Ontology extraction hit an upstream rate limit (429). "
                    f"{provider_message}"
                )
            return (
                "Ontology extraction hit an upstream rate limit (429). "
                "Retry shortly or switch to another configured model/provider."
            )
        return str(exc)

    @staticmethod
    def _provider_error_message(exc: Exception) -> str | None:
        body = getattr(exc, "body", None)
        if not isinstance(body, dict):
            return None
        error = body.get("error")
        if not isinstance(error, dict):
            return None
        metadata = error.get("metadata")
        if isinstance(metadata, dict):
            raw_message = metadata.get("raw")
            if raw_message:
                return str(raw_message)
        message = error.get("message")
        if message:
            return str(message)
        return None

    def _build_publish_snapshot(
        self,
        *,
        build_id: str | None = None,
        workspace_id: str | None = None,
        persist: bool = True,
    ) -> tuple[PublishedOntologySnapshot, dict[str, int]]:
        version_timestamp = utc_now()
        with self._database_manager.session() as session:
            build = None
            if build_id is not None:
                build = session.scalar(
                    select(OntologyBuildORM).where(OntologyBuildORM.id == build_id)
                )
                if build is None:
                    raise OntologyBuildNotFoundError(f"Ontology build '{build_id}' was not found.")
                workspace_id = build.workspace_id
            resolved_workspace_id = workspace_id or self._settings.default_workspace_id

            latest_version = self._load_latest_version(session, resolved_workspace_id)
            base_snapshot = self._snapshot_from_version(latest_version)
            draft = session.get(OntologyGraphDraftORM, resolved_workspace_id)

            entity_records = self._mutable_entities_from_snapshot(base_snapshot)
            relation_records = self._mutable_relations_from_snapshot(base_snapshot)
            entity_type_records = self._mutable_entity_type_defs_from_snapshot(base_snapshot)
            relation_type_records = self._mutable_relation_type_defs_from_snapshot(base_snapshot)
            diff_summary = {
                "entities_added": 0,
                "entities_updated": 0,
                "entities_deleted": 0,
                "relations_added": 0,
                "relations_updated": 0,
                "relations_deleted": 0,
            }

            if draft is not None:
                self._apply_draft_to_mutable_records(
                    entity_records=entity_records,
                    relation_records=relation_records,
                    entity_type_records=entity_type_records,
                    relation_type_records=relation_type_records,
                    draft=draft,
                    diff_summary=diff_summary,
                )

            if not entity_records:
                raise OntologyPublishError("No ontology entities are available to publish.")

            next_version_number = 1 if latest_version is None else latest_version.version_number + 1
            version_id = str(uuid4())
            version_title = (
                (draft.ontology_title if draft and draft.ontology_title else None)
                or (build.ontology_title if build else None)
                or (base_snapshot.version.ontology_title if base_snapshot.version else None)
                or "Ontology"
            )
            version_summary = (
                (draft.ontology_summary if draft and draft.ontology_summary else None)
                or (build.ontology_summary if build else None)
                or (base_snapshot.version.ontology_summary if base_snapshot.version else None)
            )
            version_schema = OntologyVersionResponse(
                id=version_id,
                workspace_id=resolved_workspace_id,
                version_number=next_version_number,
                source_build_id=build.id if build else "draft",
                ontology_title=version_title,
                ontology_summary=version_summary,
                created_at=version_timestamp,
                entity_type_count=len(entity_type_records),
                relation_type_count=len(relation_type_records),
                entity_count=len(entity_records),
                relation_count=len(relation_records),
            )
            version = OntologyVersionORM(
                id=version_id,
                workspace_id=resolved_workspace_id,
                version_number=next_version_number,
                source_build_id=build.id if build else "draft",
                ontology_title=version_title,
                ontology_summary=version_summary,
                created_at=version_timestamp,
            )
            if persist:
                session.add(version)

            published_entities: list[OntologyEntityResponse] = []
            published_entity_ids: dict[str, str] = {}
            for resolution_key, record in sorted(entity_records.items()):
                published_entity_id = str(uuid4())
                published_entity_ids[resolution_key] = published_entity_id
                row = OntologyEntityORM(
                    id=published_entity_id,
                    version_id=version_id,
                    workspace_id=resolved_workspace_id,
                    resolution_key=resolution_key,
                    name=record["name"],
                    entity_type=record["entity_type"],
                    aliases=record.get("aliases", []),
                    query_rules=record.get("query_rules", []),
                    source_build_id=record.get("source_build_id", build.id if build else "draft"),
                    source_document_id=record.get("source_document_id", build.document_id if build else "draft"),
                    created_at=version_timestamp,
                )
                if persist:
                    session.add(row)
                    published_entities.append(self._to_entity_schema(row))
                else:
                    published_entities.append(
                        OntologyEntityResponse(
                            id=published_entity_id,
                            version_id=version_id,
                            workspace_id=resolved_workspace_id,
                            resolution_key=resolution_key,
                            name=record["name"],
                            entity_type=record["entity_type"],
                            aliases=record.get("aliases", []),
                            query_rules=record.get("query_rules", []),
                            source_build_id=record.get("source_build_id", build.id if build else "draft"),
                            source_document_id=record.get("source_document_id", build.document_id if build else "draft"),
                            created_at=version_timestamp,
                        )
                    )

            published_entity_types: list[OntologyEntityTypeDefinitionResponse] = []
            for record in sorted(entity_type_records.values(), key=lambda item: item["name"]):
                row = OntologyEntityTypeDefinitionORM(
                    id=str(uuid4()),
                    version_id=version_id,
                    workspace_id=resolved_workspace_id,
                    name=record["name"],
                    description=record.get("description"),
                    attributes=record.get("attributes", []),
                    query_rules=record.get("query_rules", []),
                    examples=record.get("examples", []),
                    created_at=version_timestamp,
                )
                if persist:
                    session.add(row)
                    published_entity_types.append(self._to_entity_type_definition_schema(row))
                else:
                    published_entity_types.append(
                        OntologyEntityTypeDefinitionResponse(
                            id=row.id,
                            version_id=version_id,
                            workspace_id=resolved_workspace_id,
                            name=row.name,
                            description=row.description,
                            attributes=row.attributes,
                            query_rules=row.query_rules,
                            examples=row.examples,
                            created_at=version_timestamp,
                        )
                    )

            published_relation_types: list[OntologyRelationTypeDefinitionResponse] = []
            for record in sorted(relation_type_records.values(), key=lambda item: item["name"]):
                row = OntologyRelationTypeDefinitionORM(
                    id=str(uuid4()),
                    version_id=version_id,
                    workspace_id=resolved_workspace_id,
                    name=record["name"],
                    description=record.get("description"),
                    attributes=record.get("attributes", []),
                    query_rules=record.get("query_rules", []),
                    allowed_source_targets=record.get("allowed_source_targets", []),
                    created_at=version_timestamp,
                )
                if persist:
                    session.add(row)
                    published_relation_types.append(self._to_relation_type_definition_schema(row))
                else:
                    published_relation_types.append(
                        OntologyRelationTypeDefinitionResponse(
                            id=row.id,
                            version_id=version_id,
                            workspace_id=resolved_workspace_id,
                            name=row.name,
                            description=row.description,
                            attributes=row.attributes,
                            query_rules=row.query_rules,
                            allowed_source_targets=row.allowed_source_targets,
                            created_at=version_timestamp,
                        )
                    )

            published_relations: list[OntologyRelationResponse] = []
            for logical_key, record in sorted(relation_records.items()):
                source_entity_id = published_entity_ids.get(record["source_resolution_key"])
                target_entity_id = published_entity_ids.get(record["target_resolution_key"])
                if source_entity_id is None or target_entity_id is None:
                    continue
                row = OntologyRelationORM(
                    id=str(uuid4()),
                    version_id=version_id,
                    workspace_id=resolved_workspace_id,
                    source_entity_id=source_entity_id,
                    target_entity_id=target_entity_id,
                    relation_type=record["relation_type"],
                    confidence=float(record.get("confidence", 1.0)),
                    source_build_id=record.get("source_build_id", build.id if build else "draft"),
                    source_document_id=record.get("source_document_id", build.document_id if build else "draft"),
                    evidence_text=record.get("evidence_text", ""),
                    provenance=record.get("provenance", {}),
                    query_rules=record.get("query_rules", []),
                    created_at=version_timestamp,
                )
                if persist:
                    session.add(row)
                    published_relations.append(self._to_relation_schema(row))
                else:
                    published_relations.append(
                        OntologyRelationResponse(
                            id=row.id,
                            version_id=version_id,
                            workspace_id=resolved_workspace_id,
                            source_entity_id=source_entity_id,
                            target_entity_id=target_entity_id,
                            relation_type=row.relation_type,
                            confidence=row.confidence,
                            source_build_id=row.source_build_id,
                            source_document_id=row.source_document_id,
                            evidence_text=row.evidence_text,
                            provenance=row.provenance,
                            query_rules=row.query_rules,
                            created_at=version_timestamp,
                        )
                    )

            if persist:
                self._replace_published_facts(
                    session=session,
                    workspace_id=resolved_workspace_id,
                    version_id=version_id,
                    entity_records=entity_records,
                    relation_records=relation_records,
                    published_entity_ids=published_entity_ids,
                    relation_rows=published_relations,
                )

            if persist and draft is not None:
                session.delete(draft)

            return (
                PublishedOntologySnapshot(
                    workspace_id=resolved_workspace_id,
                    version=version_schema,
                    entity_type_definitions=published_entity_types,
                    relation_type_definitions=published_relation_types,
                    entities=published_entities,
                    relations=published_relations,
                ),
                diff_summary,
            )

    def _load_graphiti_chunks_for_snapshot(
        self,
        snapshot: PublishedOntologySnapshot,
    ) -> list[GraphitiDocumentChunk]:
        doc_ids = {e.source_document_id for e in snapshot.entities if e.source_document_id}
        if not doc_ids:
            return []
        with self._database_manager.session() as session:
            rows = session.scalars(
                select(DocumentChunkORM).where(DocumentChunkORM.document_id.in_(doc_ids))
            ).all()
            artifacts = session.scalars(
                select(DocumentArtifactORM).where(
                    DocumentArtifactORM.document_id.in_(doc_ids),
                    DocumentArtifactORM.artifact_type == "markdown",
                )
            ).all()
            documents = session.scalars(select(DocumentORM).where(DocumentORM.id.in_(doc_ids))).all()
        if rows:
            return [
                GraphitiDocumentChunk(
                    chunk_id=row.chunk_id,
                    document_id=row.document_id,
                    document_title=row.document_title,
                    text=row.text,
                    created_at=row.created_at,
                )
                for row in rows
            ]

        artifact_map = {artifact.document_id: artifact for artifact in artifacts}
        title_map = {document.id: document.title for document in documents}
        fallback_chunks: list[GraphitiDocumentChunk] = []
        for doc_id in doc_ids:
            artifact = artifact_map.get(doc_id)
            if artifact is None:
                continue
            content = self._object_store.get_document_binary(doc_id, artifact.object_key)
            if content:
                text = content.decode("utf-8")
            else:
                inline_text = (artifact.metadata_json or {}).get("inline_text")
                text = inline_text if isinstance(inline_text, str) else ""
            if not text.strip():
                continue
            fallback_chunks.append(
                GraphitiDocumentChunk(
                    chunk_id=f"{doc_id}-markdown",
                    document_id=doc_id,
                    document_title=title_map.get(doc_id) or doc_id,
                    text=text[:120_000],
                    created_at=artifact.created_at,
                )
            )
        return fallback_chunks

    def _get_relational_graph(self, workspace_id: str) -> OntologyGraphResponse:
        snapshot, draft_summary = self._build_workspace_snapshot(
            workspace_id=workspace_id,
            include_draft=False,
        )
        return OntologyGraphResponse(
            workspace_id=workspace_id,
            version=snapshot.version,
            ontology_title=snapshot.version.ontology_title if snapshot.version else None,
            ontology_summary=snapshot.version.ontology_summary if snapshot.version else None,
            entity_type_definitions=snapshot.entity_type_definitions,
            relation_type_definitions=snapshot.relation_type_definitions,
            entities=snapshot.entities,
            relations=snapshot.relations,
            draft_summary=draft_summary,
            graphiti_indexed=self._graph_publisher.graphiti_indexed_for(workspace_id),
        )

    def _build_workspace_snapshot(
        self,
        *,
        workspace_id: str,
        include_draft: bool,
    ) -> tuple[PublishedOntologySnapshot, OntologyGraphDraftSummaryResponse]:
        with self._database_manager.session() as session:
            version = self._load_latest_version(session, workspace_id)
            snapshot = self._snapshot_from_version(version)
            draft = session.get(OntologyGraphDraftORM, workspace_id)
            if not include_draft or draft is None:
                return snapshot, self._draft_summary(draft)

            entity_records = self._mutable_entities_from_snapshot(snapshot)
            relation_records = self._mutable_relations_from_snapshot(snapshot)
            entity_type_records = self._mutable_entity_type_defs_from_snapshot(snapshot)
            relation_type_records = self._mutable_relation_type_defs_from_snapshot(snapshot)
            self._apply_draft_to_mutable_records(
                entity_records=entity_records,
                relation_records=relation_records,
                entity_type_records=entity_type_records,
                relation_type_records=relation_type_records,
                draft=draft,
                diff_summary=None,
            )
            preview_version = snapshot.version
            if preview_version is not None and (draft.ontology_title or draft.ontology_summary):
                preview_version = preview_version.model_copy(
                    update={
                        "ontology_title": draft.ontology_title or preview_version.ontology_title,
                        "ontology_summary": draft.ontology_summary or preview_version.ontology_summary,
                        "entity_count": len(entity_records),
                        "relation_count": len(relation_records),
                        "entity_type_count": len(entity_type_records),
                        "relation_type_count": len(relation_type_records),
                    }
                )
            return (
                PublishedOntologySnapshot(
                    workspace_id=workspace_id,
                    version=preview_version,
                    entity_type_definitions=self._entity_type_schemas_from_records(
                        workspace_id,
                        entity_type_records,
                    ),
                    relation_type_definitions=self._relation_type_schemas_from_records(
                        workspace_id,
                        relation_type_records,
                    ),
                    entities=self._entity_schemas_from_records(workspace_id, preview_version, entity_records),
                    relations=self._relation_schemas_from_records(workspace_id, preview_version, entity_records, relation_records),
                ),
                self._draft_summary(draft),
            )

    @staticmethod
    def _load_latest_version(session, workspace_id: str) -> OntologyVersionORM | None:
        return session.scalar(
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

    def _snapshot_from_version(self, version: OntologyVersionORM | None) -> PublishedOntologySnapshot:
        if version is None:
            return PublishedOntologySnapshot(
                workspace_id=self._settings.default_workspace_id,
                version=None,
                entity_type_definitions=[],
                relation_type_definitions=[],
                entities=[],
                relations=[],
            )
        return PublishedOntologySnapshot(
            workspace_id=version.workspace_id,
            version=self._to_version_schema(version),
            entity_type_definitions=[
                self._to_entity_type_definition_schema(item) for item in version.entity_types
            ],
            relation_type_definitions=[
                self._to_relation_type_definition_schema(item) for item in version.relation_types
            ],
            entities=[self._to_entity_schema(item) for item in version.entities],
            relations=[self._to_relation_schema(item) for item in version.relations],
        )

    @staticmethod
    def _mutable_entities_from_snapshot(snapshot: PublishedOntologySnapshot) -> dict[str, dict]:
        return {
            entity.resolution_key: {
                "id": entity.id,
                "resolution_key": entity.resolution_key,
                "name": entity.name,
                "entity_type": entity.entity_type,
                "aliases": list(entity.aliases),
                "query_rules": [rule.model_dump() for rule in entity.query_rules],
                "source_build_id": entity.source_build_id,
                "source_document_id": entity.source_document_id,
            }
            for entity in snapshot.entities
        }

    @staticmethod
    def _mutable_relations_from_snapshot(snapshot: PublishedOntologySnapshot) -> dict[tuple[str, str, str], dict]:
        entity_keys = {entity.id: entity.resolution_key for entity in snapshot.entities}
        records: dict[tuple[str, str, str], dict] = {}
        for relation in snapshot.relations:
            source_key = entity_keys.get(relation.source_entity_id)
            target_key = entity_keys.get(relation.target_entity_id)
            if not source_key or not target_key:
                continue
            logical_key = (source_key, target_key, relation.relation_type)
            records[logical_key] = {
                "id": relation.id,
                "source_resolution_key": source_key,
                "target_resolution_key": target_key,
                "relation_type": relation.relation_type,
                "confidence": relation.confidence,
                "source_build_id": relation.source_build_id,
                "source_document_id": relation.source_document_id,
                "evidence_text": relation.evidence_text,
                "provenance": deepcopy(relation.provenance),
                "query_rules": [rule.model_dump() for rule in relation.query_rules],
            }
        return records

    @staticmethod
    def _mutable_entity_type_defs_from_snapshot(snapshot: PublishedOntologySnapshot) -> dict[str, dict]:
        return {
            item.name: {
                "id": item.id,
                "name": item.name,
                "description": item.description,
                "attributes": [
                    entry.model_dump() if hasattr(entry, "model_dump") else deepcopy(entry)
                    for entry in item.attributes
                ],
                "query_rules": [
                    entry.model_dump() if hasattr(entry, "model_dump") else deepcopy(entry)
                    for entry in item.query_rules
                ],
                "examples": list(item.examples),
            }
            for item in snapshot.entity_type_definitions
        }

    @staticmethod
    def _mutable_relation_type_defs_from_snapshot(snapshot: PublishedOntologySnapshot) -> dict[str, dict]:
        return {
            item.name: {
                "id": item.id,
                "name": item.name,
                "description": item.description,
                "attributes": [
                    entry.model_dump() if hasattr(entry, "model_dump") else deepcopy(entry)
                    for entry in item.attributes
                ],
                "query_rules": [
                    entry.model_dump() if hasattr(entry, "model_dump") else deepcopy(entry)
                    for entry in item.query_rules
                ],
                "allowed_source_targets": [
                    entry.model_dump() if hasattr(entry, "model_dump") else deepcopy(entry)
                    for entry in item.allowed_source_targets
                ],
            }
            for item in snapshot.relation_type_definitions
        }

    def _apply_draft_to_mutable_records(
        self,
        *,
        entity_records: dict[str, dict],
        relation_records: dict[tuple[str, str, str], dict],
        entity_type_records: dict[str, dict],
        relation_type_records: dict[str, dict],
        draft: OntologyGraphDraftORM,
        diff_summary: dict[str, int] | None,
    ) -> None:
        resolution_lookup = {record.get("id", key): key for key, record in entity_records.items()}
        for patch in draft.node_patches or []:
            patch_id = str(patch["id"])
            if patch.get("op") == "delete":
                resolution_key = resolution_lookup.get(patch_id, patch_id)
                if resolution_key in entity_records:
                    entity_records.pop(resolution_key, None)
                    relation_records_keys = [
                        key for key in relation_records if resolution_key in key[:2]
                    ]
                    for logical_key in relation_records_keys:
                        relation_records.pop(logical_key, None)
                    if diff_summary is not None:
                        diff_summary["entities_deleted"] += 1
                continue
            record = {
                "id": patch_id,
                "resolution_key": patch.get("resolution_key") or resolution_lookup.get(patch_id) or self._slugify(str(patch["name"])),
                "name": patch["name"],
                "entity_type": patch["entity_type"],
                "aliases": list(patch.get("aliases", [])),
                "query_rules": deepcopy(patch.get("query_rules", [])),
                "source_build_id": patch.get("source_build_id", "draft"),
                "source_document_id": patch.get("source_document_id", "draft"),
            }
            is_update = record["resolution_key"] in entity_records
            entity_records[record["resolution_key"]] = record
            resolution_lookup[patch_id] = record["resolution_key"]
            if diff_summary is not None:
                diff_summary["entities_updated" if is_update else "entities_added"] += 1
            entity_type_records.setdefault(
                record["entity_type"],
                {
                    "id": f"entity-type:{record['entity_type']}",
                    "name": record["entity_type"],
                    "description": f"Draft entity type for {record['entity_type']}.",
                    "attributes": [],
                    "examples": [],
                },
            )
            entity_type_records[record["entity_type"]]["examples"] = self._append_example(
                entity_type_records[record["entity_type"]].get("examples", []),
                record["name"],
            )

        for patch in draft.relation_patches or []:
            patch_id = str(patch["id"])
            source_resolution_key = resolution_lookup.get(str(patch.get("source_entity_id")), str(patch.get("source_entity_id")))
            target_resolution_key = resolution_lookup.get(str(patch.get("target_entity_id")), str(patch.get("target_entity_id")))
            logical_key = (source_resolution_key, target_resolution_key, str(patch.get("relation_type")))
            if patch.get("op") == "delete":
                removed = False
                for existing_key, existing_value in list(relation_records.items()):
                    if existing_value.get("id") == patch_id or existing_key == logical_key:
                        relation_records.pop(existing_key, None)
                        removed = True
                if removed and diff_summary is not None:
                    diff_summary["relations_deleted"] += 1
                continue
            self._ensure_resolution_keys_exist(entity_records, source_resolution_key, target_resolution_key)
            is_update = logical_key in relation_records
            relation_records[logical_key] = {
                "id": patch_id,
                "source_resolution_key": source_resolution_key,
                "target_resolution_key": target_resolution_key,
                "relation_type": patch["relation_type"],
                "confidence": float(patch.get("confidence", 1.0)),
                "source_build_id": patch.get("source_build_id", "draft"),
                "source_document_id": patch.get("source_document_id", "draft"),
                "evidence_text": patch.get("evidence_text", ""),
                "provenance": deepcopy(patch.get("provenance", {"source": "draft_editor"})),
                "query_rules": deepcopy(patch.get("query_rules", [])),
            }
            if diff_summary is not None:
                diff_summary["relations_updated" if is_update else "relations_added"] += 1
            self._ensure_relation_type_record(
                relation_type_records,
                str(patch["relation_type"]),
                str(entity_records[source_resolution_key]["entity_type"]),
                str(entity_records[target_resolution_key]["entity_type"]),
            )

        for patch in draft.entity_type_patches or []:
            target_name = str(patch.get("name") or patch.get("id"))
            if patch.get("op") == "delete":
                entity_type_records.pop(target_name, None)
                continue
            entity_type_records[target_name] = {
                "id": str(patch.get("id") or target_name),
                "name": target_name,
                "description": patch.get("description"),
                "attributes": deepcopy(patch.get("attributes", [])),
                "query_rules": deepcopy(patch.get("query_rules", [])),
                "examples": list(patch.get("examples", [])),
            }

        for patch in draft.relation_type_patches or []:
            target_name = str(patch.get("name") or patch.get("id"))
            if patch.get("op") == "delete":
                relation_type_records.pop(target_name, None)
                continue
            relation_type_records[target_name] = {
                "id": str(patch.get("id") or target_name),
                "name": target_name,
                "description": patch.get("description"),
                "attributes": deepcopy(patch.get("attributes", [])),
                "query_rules": deepcopy(patch.get("query_rules", [])),
                "allowed_source_targets": deepcopy(patch.get("allowed_source_targets", [])),
            }

    def _entity_type_schemas_from_records(
        self,
        workspace_id: str,
        records: dict[str, dict],
    ) -> list[OntologyEntityTypeDefinitionResponse]:
        return [
            OntologyEntityTypeDefinitionResponse(
                id=str(record.get("id") or name),
                workspace_id=workspace_id,
                name=str(record["name"]),
                description=record.get("description"),
                attributes=record.get("attributes", []),
                query_rules=record.get("query_rules", []),
                examples=record.get("examples", []),
            )
            for name, record in sorted(records.items())
        ]

    def _relation_type_schemas_from_records(
        self,
        workspace_id: str,
        records: dict[str, dict],
    ) -> list[OntologyRelationTypeDefinitionResponse]:
        return [
            OntologyRelationTypeDefinitionResponse(
                id=str(record.get("id") or name),
                workspace_id=workspace_id,
                name=str(record["name"]),
                description=record.get("description"),
                attributes=record.get("attributes", []),
                query_rules=record.get("query_rules", []),
                allowed_source_targets=record.get("allowed_source_targets", []),
            )
            for name, record in sorted(records.items())
        ]

    def _entity_schemas_from_records(
        self,
        workspace_id: str,
        version: OntologyVersionResponse | None,
        records: dict[str, dict],
    ) -> list[OntologyEntityResponse]:
        version_id = version.id if version is not None else "draft"
        return [
            OntologyEntityResponse(
                id=str(record.get("id") or resolution_key),
                version_id=version_id,
                workspace_id=workspace_id,
                resolution_key=resolution_key,
                name=str(record["name"]),
                entity_type=str(record["entity_type"]),
                aliases=list(record.get("aliases", [])),
                query_rules=record.get("query_rules", []),
                source_build_id=str(record.get("source_build_id", "draft")),
                source_document_id=str(record.get("source_document_id", "draft")),
            )
            for resolution_key, record in sorted(records.items())
        ]

    def _relation_schemas_from_records(
        self,
        workspace_id: str,
        version: OntologyVersionResponse | None,
        entity_records: dict[str, dict],
        relation_records: dict[tuple[str, str, str], dict],
    ) -> list[OntologyRelationResponse]:
        version_id = version.id if version is not None else "draft"
        entity_ids = {
            resolution_key: str(record.get("id") or resolution_key)
            for resolution_key, record in entity_records.items()
        }
        responses: list[OntologyRelationResponse] = []
        for logical_key, record in sorted(relation_records.items()):
            responses.append(
                OntologyRelationResponse(
                    id=str(record.get("id") or ":".join(logical_key)),
                    version_id=version_id,
                    workspace_id=workspace_id,
                    source_entity_id=entity_ids[record["source_resolution_key"]],
                    target_entity_id=entity_ids[record["target_resolution_key"]],
                    relation_type=str(record["relation_type"]),
                    confidence=float(record.get("confidence", 1.0)),
                    source_build_id=str(record.get("source_build_id", "draft")),
                    source_document_id=str(record.get("source_document_id", "draft")),
                    evidence_text=str(record.get("evidence_text", "")),
                    provenance=deepcopy(record.get("provenance", {})),
                    query_rules=record.get("query_rules", []),
                )
            )
        return responses

    @staticmethod
    def _draft_summary(draft: OntologyGraphDraftORM | None) -> OntologyGraphDraftSummaryResponse:
        return OntologyGraphDraftSummaryResponse(
            based_on_version_id=draft.based_on_version_id if draft else None,
            has_changes=bool(
                draft
                and (
                    draft.node_patches
                    or draft.relation_patches
                    or draft.entity_type_patches
                    or draft.relation_type_patches
                    or draft.ontology_title
                    or draft.ontology_summary
                )
            ),
            node_patch_count=len(draft.node_patches or []) if draft else 0,
            relation_patch_count=len(draft.relation_patches or []) if draft else 0,
            entity_type_patch_count=len(draft.entity_type_patches or []) if draft else 0,
            relation_type_patch_count=len(draft.relation_type_patches or []) if draft else 0,
            updated_at=draft.updated_at if draft else None,
        )

    def _upsert_draft_patch(self, workspace_id: str, field_name: str, patch_id: str, patch: dict) -> None:
        with self._database_manager.session() as session:
            draft = self._ensure_draft(session, workspace_id)
            items = list(getattr(draft, field_name) or [])
            items = [item for item in items if str(item.get("id")) != patch_id]
            items.append(patch)
            setattr(draft, field_name, items)
            draft.updated_at = utc_now()

    def _ensure_draft(self, session, workspace_id: str) -> OntologyGraphDraftORM:
        draft = session.get(OntologyGraphDraftORM, workspace_id)
        if draft is not None:
            return draft
        latest_version = self._load_latest_version(session, workspace_id)
        draft = OntologyGraphDraftORM(
            workspace_id=workspace_id,
            based_on_version_id=latest_version.id if latest_version else None,
            ontology_title=latest_version.ontology_title if latest_version else None,
            ontology_summary=latest_version.ontology_summary if latest_version else None,
            node_patches=[],
            relation_patches=[],
            entity_type_patches=[],
            relation_type_patches=[],
            created_at=utc_now(),
            updated_at=utc_now(),
        )
        session.add(draft)
        return draft

    def _existing_node_patch(self, workspace_id: str, node_id: str) -> dict:
        snapshot, _ = self._build_workspace_snapshot(workspace_id=workspace_id, include_draft=True)
        for entity in snapshot.entities:
            if entity.id == node_id:
                return {
                    "id": node_id,
                    "name": entity.name,
                    "entity_type": entity.entity_type,
                    "resolution_key": entity.resolution_key,
                    "aliases": list(entity.aliases),
                    "query_rules": [rule.model_dump() for rule in entity.query_rules],
                    "source_document_id": entity.source_document_id,
                    "source_build_id": entity.source_build_id,
                }
        raise OntologyDraftError(f"Draft node '{node_id}' was not found.")

    def _existing_relation_patch(self, workspace_id: str, relation_id: str) -> dict:
        snapshot, _ = self._build_workspace_snapshot(workspace_id=workspace_id, include_draft=True)
        for relation in snapshot.relations:
            if relation.id == relation_id:
                return {
                    "id": relation_id,
                    "source_entity_id": relation.source_entity_id,
                    "target_entity_id": relation.target_entity_id,
                    "relation_type": relation.relation_type,
                    "confidence": relation.confidence,
                    "evidence_text": relation.evidence_text,
                    "query_rules": [rule.model_dump() for rule in relation.query_rules],
                    "source_document_id": relation.source_document_id,
                    "source_build_id": relation.source_build_id,
                }
        raise OntologyDraftError(f"Draft relation '{relation_id}' was not found.")

    def _delete_relations_for_missing_node(self, workspace_id: str, node_id: str) -> None:
        with self._database_manager.session() as session:
            draft = self._ensure_draft(session, workspace_id)
            relation_patches = []
            for patch in draft.relation_patches or []:
                if patch.get("source_entity_id") == node_id or patch.get("target_entity_id") == node_id:
                    relation_patches.append({"id": patch["id"], "op": "delete"})
                else:
                    relation_patches.append(patch)
            draft.relation_patches = relation_patches
            draft.updated_at = utc_now()

    def _ensure_relation_endpoints_exist(self, workspace_id: str, source_entity_id: str, target_entity_id: str) -> None:
        snapshot, _ = self._build_workspace_snapshot(workspace_id=workspace_id, include_draft=True)
        node_ids = {entity.id for entity in snapshot.entities}
        if source_entity_id not in node_ids or target_entity_id not in node_ids:
            raise OntologyDraftError("Draft relation endpoints must reference existing nodes.")

    @staticmethod
    def _ensure_resolution_keys_exist(
        entity_records: dict[str, dict],
        source_resolution_key: str,
        target_resolution_key: str,
    ) -> None:
        if source_resolution_key not in entity_records or target_resolution_key not in entity_records:
            raise OntologyDraftError("Draft relation endpoints must reference existing nodes.")

    @staticmethod
    def _ensure_relation_type_record(
        relation_type_records: dict[str, dict],
        relation_type: str,
        source_entity_type: str,
        target_entity_type: str,
    ) -> None:
        relation_type_records.setdefault(
            relation_type,
            {
                "id": f"relation-type:{relation_type}",
                "name": relation_type,
                "description": f"Derived relation type for {relation_type}.",
                "attributes": [],
                "query_rules": [],
                "allowed_source_targets": [],
            },
        )
        pair = {
            "source_entity_type": source_entity_type,
            "target_entity_type": target_entity_type,
        }
        if pair not in relation_type_records[relation_type]["allowed_source_targets"]:
            relation_type_records[relation_type]["allowed_source_targets"].append(pair)

    @staticmethod
    def _append_example(existing: list[str], example: str) -> list[str]:
        values = list(existing)
        if example not in values:
            values.append(example)
        return values[:5]

    @staticmethod
    def _slugify(value: str) -> str:
        normalized = "".join(char.lower() if char.isalnum() else "-" for char in value).strip("-")
        while "--" in normalized:
            normalized = normalized.replace("--", "-")
        return normalized or str(uuid4())

    def _clear_draft(self, workspace_id: str) -> None:
        with self._database_manager.session() as session:
            draft = session.get(OntologyGraphDraftORM, workspace_id)
            if draft is not None:
                session.delete(draft)

    def _empty_build_for_publish(self, workspace_id: str) -> OntologyBuildResponse:
        timestamp = utc_now()
        return OntologyBuildResponse(
            id="draft-publish",
            document_id="draft",
            workspace_id=workspace_id,
            status=OntologyBuildStatus.published,
            ontology_title=None,
            ontology_summary=None,
            merge_mode=OntologyMergeMode.append,
            created_at=timestamp,
            updated_at=timestamp,
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
                metadata_json={},
                started_at=None,
                finished_at=None,
            )
            for name in ONTOLOGY_BUILD_STEP_NAMES
        ]

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
        steps_by_build = self._load_build_steps(session, build_ids)
        return [
            self._to_build_schema(
                build,
                steps=steps_by_build.get(build.id, []),
            )
            for build in builds
        ]

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
        steps: list[OntologyBuildStepORM],
    ) -> OntologyBuildResponse:
        entity_count, relation_count = self._counts_from_steps(steps)
        return OntologyBuildResponse(
            id=build.id,
            document_id=build.document_id,
            workspace_id=build.workspace_id,
            status=build.status,
            domain=build.domain,
            ontology_title=build.ontology_title,
            ontology_summary=build.ontology_summary,
            merge_mode=build.merge_mode,
            extraction_provider=build.extraction_provider,
            extraction_model=build.extraction_model,
            created_at=build.created_at,
            started_at=build.started_at,
            finished_at=build.finished_at,
            updated_at=build.updated_at,
            error_message=build.error_message,
            published_version_id=build.published_version_id,
            entity_count=entity_count,
            relation_count=relation_count,
            pending_entity_count=0,
            pending_relation_count=0,
            entity_type_definitions=[],
            relation_type_definitions=[],
            steps=[self._to_step_schema(step) for step in steps],
        )

    @staticmethod
    def _counts_from_steps(steps: list[OntologyBuildStepORM]) -> tuple[int, int]:
        entity_count = 0
        relation_count = 0
        for step in steps:
            metadata = step.metadata_json or {}
            trace = metadata.get("safe_trace") if isinstance(metadata, dict) else None
            if not isinstance(trace, dict):
                continue
            if step.name == "extract_entities":
                value = trace.get("entity_count")
                if isinstance(value, int):
                    entity_count = value
            if step.name == "extract_relations":
                value = trace.get("relation_count")
                if isinstance(value, int):
                    relation_count = value
        return entity_count, relation_count

    @classmethod
    def _serialize_query_rules(cls, rules: list[object] | None) -> list[dict]:
        payload: list[dict] = []
        for rule in rules or []:
            if is_dataclass(rule):
                candidate = asdict(rule)
            elif hasattr(rule, "__dict__"):
                candidate = deepcopy(getattr(rule, "__dict__", {}))
            elif isinstance(rule, dict):
                candidate = deepcopy(rule)
            else:
                continue
            if not isinstance(candidate, dict):
                continue
            route = str(candidate.get("query_route") or "").strip().lower()
            if route not in {"graph", "sql_facts", "hybrid"}:
                continue
            scope = str(candidate.get("scope") or "entity_type").strip()
            rule_id = str(candidate.get("rule_id") or "").strip() or f"rule:{scope}:{route}:{len(payload)+1}"
            payload.append(
                {
                    "rule_id": rule_id,
                    "scope": scope,
                    "query_route": route,
                    "trigger_keywords": [str(x) for x in candidate.get("trigger_keywords", []) if str(x).strip()],
                    "intent_tags": [str(x) for x in candidate.get("intent_tags", []) if str(x).strip()],
                    "required_fields": [str(x) for x in candidate.get("required_fields", []) if str(x).strip()],
                    "aggregation": str(candidate.get("aggregation") or "latest"),
                    "confidence_threshold": candidate.get("confidence_threshold"),
                    "fallback_route": candidate.get("fallback_route"),
                    "metadata": candidate.get("metadata") if isinstance(candidate.get("metadata"), dict) else {},
                }
            )
        return payload

    @classmethod
    def _merge_rule_dicts(cls, existing: list[dict] | None, incoming: list[object] | None) -> list[dict]:
        merged: dict[str, dict] = {str(item.get("rule_id")): deepcopy(item) for item in (existing or []) if isinstance(item, dict) and item.get("rule_id")}
        for item in cls._serialize_query_rules(incoming):
            merged[str(item["rule_id"])] = item
        return list(merged.values())

    @staticmethod
    def _fact_dicts(facts: list[dict] | None) -> list[dict]:
        return [deepcopy(fact) for fact in (facts or []) if isinstance(fact, dict)]

    @classmethod
    def _serialize_facts(cls, facts: list[object] | None) -> list[dict]:
        payload: list[dict] = []
        for fact in facts or []:
            if is_dataclass(fact):
                candidate = asdict(fact)
            elif hasattr(fact, "__dict__"):
                candidate = deepcopy(getattr(fact, "__dict__", {}))
            elif isinstance(fact, dict):
                candidate = deepcopy(fact)
            else:
                continue
            if not isinstance(candidate, dict):
                continue
            metric_key = str(candidate.get("metric_key") or "").strip()
            if not metric_key:
                continue
            payload.append(
                {
                    "metric_key": metric_key,
                    "value_num": candidate.get("value_num"),
                    "value_text": candidate.get("value_text"),
                    "value_bool": candidate.get("value_bool"),
                    "unit": candidate.get("unit"),
                    "observed_at": candidate.get("observed_at"),
                    "source_chunk_id": candidate.get("source_chunk_id"),
                    "metadata": candidate.get("metadata") if isinstance(candidate.get("metadata"), dict) else {},
                }
            )
        return payload

    @staticmethod
    def _parse_observed_at(value: object) -> datetime | None:
        if value is None or value == "":
            return None
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            try:
                return datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError:
                return None
        return None

    def _replace_published_facts(
        self,
        *,
        session,  # noqa: ANN001
        workspace_id: str,
        version_id: str,
        entity_records: dict[str, dict],
        relation_records: dict[tuple[str, str, str], dict],
        published_entity_ids: dict[str, str],
        relation_rows: list[OntologyRelationResponse],
    ) -> None:
        session.execute(delete(OntologyEntityFactORM).where(OntologyEntityFactORM.version_id == version_id))
        session.execute(delete(OntologyRelationFactORM).where(OntologyRelationFactORM.version_id == version_id))

        for resolution_key, record in entity_records.items():
            entity_id = published_entity_ids.get(resolution_key)
            if entity_id is None:
                continue
            for fact in self._fact_dicts(record.get("facts", [])):
                session.add(
                    OntologyEntityFactORM(
                        id=str(uuid4()),
                        workspace_id=workspace_id,
                        version_id=version_id,
                        entity_id=entity_id,
                        metric_key=str(fact.get("metric_key")),
                        value_num=fact.get("value_num"),
                        value_text=fact.get("value_text"),
                        value_bool=fact.get("value_bool"),
                        unit=fact.get("unit"),
                        observed_at=self._parse_observed_at(fact.get("observed_at")),
                        source_document_id=record.get("source_document_id"),
                        source_chunk_id=fact.get("source_chunk_id"),
                        metadata_json=fact.get("metadata", {}),
                        created_at=utc_now(),
                    )
                )

        entity_key_by_id = {entity_id: key for key, entity_id in published_entity_ids.items()}
        relation_id_by_key: dict[tuple[str, str, str], str] = {}
        for relation in relation_rows:
            source_key = entity_key_by_id.get(relation.source_entity_id)
            target_key = entity_key_by_id.get(relation.target_entity_id)
            if source_key and target_key:
                relation_id_by_key[(source_key, target_key, relation.relation_type)] = relation.id
        for logical_key, record in relation_records.items():
            relation_id = relation_id_by_key.get(logical_key)
            if relation_id is None:
                continue
            for fact in self._fact_dicts(record.get("facts", [])):
                session.add(
                    OntologyRelationFactORM(
                        id=str(uuid4()),
                        workspace_id=workspace_id,
                        version_id=version_id,
                        relation_id=relation_id,
                        metric_key=str(fact.get("metric_key")),
                        value_num=fact.get("value_num"),
                        value_text=fact.get("value_text"),
                        value_bool=fact.get("value_bool"),
                        unit=fact.get("unit"),
                        observed_at=self._parse_observed_at(fact.get("observed_at")),
                        source_document_id=record.get("source_document_id"),
                        source_chunk_id=fact.get("source_chunk_id"),
                        metadata_json=fact.get("metadata", {}),
                        created_at=utc_now(),
                    )
                )

    @staticmethod
    def _to_step_schema(step: OntologyBuildStepORM) -> OntologyBuildStepResponse:
        return OntologyBuildStepResponse(
            id=step.id,
            name=step.name,
            status=step.status,
            detail=step.detail,
            metadata=step.metadata_json or {},
            started_at=step.started_at,
            finished_at=step.finished_at,
        )

    def _to_version_schema(self, version: OntologyVersionORM) -> OntologyVersionResponse:
        return OntologyVersionResponse(
            id=version.id,
            workspace_id=version.workspace_id,
            version_number=version.version_number,
            source_build_id=version.source_build_id,
            ontology_title=version.ontology_title,
            ontology_summary=version.ontology_summary,
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
            query_rules=entity_type.query_rules or [],
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
            query_rules=relation_type.query_rules or [],
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
            query_rules=entity.query_rules or [],
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
            query_rules=relation.query_rules or [],
            created_at=relation.created_at,
        )

    @staticmethod
    def _step_sort_key(step: OntologyBuildStepORM) -> int:
        if step.name in ONTOLOGY_BUILD_STEP_NAMES:
            return ONTOLOGY_BUILD_STEP_NAMES.index(step.name)
        return len(ONTOLOGY_BUILD_STEP_NAMES)
