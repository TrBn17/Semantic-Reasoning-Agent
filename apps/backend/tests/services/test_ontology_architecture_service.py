from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select

from semantic_reasoning_agent.core.config import Settings
from semantic_reasoning_agent.domain.ontology.models import (
    ExtractedEntity,
    ExtractedRelation,
    ExtractionResult,
)
from semantic_reasoning_agent.persistence.database import DatabaseManager
from semantic_reasoning_agent.persistence.models.base import Base
from semantic_reasoning_agent.persistence.models.documents import DocumentChunkORM, DocumentORM
from semantic_reasoning_agent.persistence.models.ontology import (
    OntologyBuildORM,
    OntologyCandidateEntityORM,
    OntologyCandidateRelationORM,
)
from semantic_reasoning_agent.persistence.repositories.ontology_repo import OntologyRepository
from semantic_reasoning_agent.schemas.documents import DocumentStatus
from semantic_reasoning_agent.schemas.ontology import OntologyBuildCreateRequest
from semantic_reasoning_agent.services.ontology_architecture_service import (
    OntologyArchitectureService,
)
from semantic_reasoning_agent.services.ontology_service import OntologyService


class _FakeModelResolver:
    def resolve_task_model(self, task_type: str, workspace_id: str | None = None, agent_profile_id: str | None = None) -> tuple[str, str]:
        return "anthropic", "fake-model"

    def is_ready(self, provider: str, model: str, workspace_id: str | None = None) -> bool:
        return False

    def get_provider_runtime_config(self, provider: str, workspace_id: str | None = None) -> dict[str, str | None]:
        return {}


class _NoopTaskDispatcher:
    def enqueue_ontology_build_processing(self, build_id: str) -> None:
        raise AssertionError("queueing should not happen in this test")


class _NoopGraphStore:
    def is_enabled(self) -> bool:
        return False

    def verify_connection(self) -> None:
        return None

    def sync_published_graph(self, snapshot) -> None:  # noqa: ANN001
        return None

    def get_graph(self, workspace_id: str):
        raise AssertionError("graph reads are not expected in this test")

    def delete_workspace(self, workspace_id: str) -> None:
        return None


@dataclass
class _FakeExtractor:
    seen_draft_id: str | None = None

    def classify_document_domain(self, chunks) -> str:  # noqa: ANN001
        return "pending"

    def extract_ontology_candidates(self, chunks, workspace_id: str | None = None, architecture_draft=None):  # noqa: ANN001
        self.seen_draft_id = None if architecture_draft is None else architecture_draft.draft_id
        return ExtractionResult(
            domain="policy_graph",
            entities=[
                ExtractedEntity(
                    name="Beta System",
                    canonical_name="beta_system",
                    resolution_key="beta_system",
                    entity_type="system",
                    confidence=0.93,
                    source_chunk_id=chunks[0].chunk_id,
                    evidence_text="Beta System approves requests.",
                    provenance={},
                    aliases={"beta"},
                )
            ],
            relations=[
                ExtractedRelation(
                    source_resolution_key="beta_system",
                    target_resolution_key="audit_service",
                    source_name="beta_system",
                    target_name="audit_service",
                    relation_type="depends_on",
                    confidence=0.77,
                    source_chunk_id=chunks[0].chunk_id,
                    evidence_text="Beta System depends on Audit Service.",
                    provenance={},
                )
            ],
        )


def _settings() -> Settings:
    return Settings(
        database_url="sqlite+pysqlite:///:memory:",
        ontology_llm_enabled=False,
        neo4j_enabled=False,
    )


def _database_manager() -> DatabaseManager:
    import semantic_reasoning_agent.persistence.models.agent_profiles  # noqa: F401
    import semantic_reasoning_agent.persistence.models.conversations  # noqa: F401
    import semantic_reasoning_agent.persistence.models.documents  # noqa: F401
    import semantic_reasoning_agent.persistence.models.ontology  # noqa: F401
    import semantic_reasoning_agent.persistence.models.providers  # noqa: F401
    import semantic_reasoning_agent.persistence.models.runtime  # noqa: F401

    manager = DatabaseManager(_settings())
    Base.metadata.create_all(manager.engine, checkfirst=False)
    return manager


def _seed_indexed_document(db: DatabaseManager) -> None:
    with db.session() as session:
        session.add(
            DocumentORM(
                id="doc-1",
                title="Policy Notes",
                filename="policy.txt",
                workspace_id="ws-1",
                document_type="txt",
                status=DocumentStatus.indexed.value,
                parser_version="test",
                chunk_count=2,
                tags=[],
                source_url="",
                binary_content=b"policy",
            )
        )
        session.add_all(
            [
                DocumentChunkORM(
                    chunk_id="chunk-1",
                    document_id="doc-1",
                    workspace_id="ws-1",
                    document_title="Policy Notes",
                    document_type="txt",
                    text="Beta System approves requests. Audit Service stores approvals.",
                    chunk_index=0,
                    source_url="",
                    parser_version="test",
                    embedding={},
                    page_number=None,
                    section_title=None,
                    heading_path=None,
                    table_index=None,
                    sheet_name=None,
                    detected_table_id=None,
                    row_start=None,
                    row_end=None,
                    column_headers=[],
                ),
                DocumentChunkORM(
                    chunk_id="chunk-2",
                    document_id="doc-1",
                    workspace_id="ws-1",
                    document_title="Policy Notes",
                    document_type="txt",
                    text="Audit Service validates policy updates before publication.",
                    chunk_index=1,
                    source_url="",
                    parser_version="test",
                    embedding={},
                    page_number=None,
                    section_title=None,
                    heading_path=None,
                    table_index=None,
                    sheet_name=None,
                    detected_table_id=None,
                    row_start=None,
                    row_end=None,
                    column_headers=[],
                ),
            ]
        )


def test_architecture_service_creates_active_draft_with_evidence_links() -> None:
    db = _database_manager()
    repo = OntologyRepository(db)
    service = OntologyArchitectureService(
        settings=_settings(),
        database_manager=db,
        ontology_repo=repo,
        model_config_service=_FakeModelResolver(),
    )

    draft = service.ensure_active_draft(
        workspace_id="ws-1",
        source_document_ids=["doc-1"],
        source_build_id=None,
        chunk_samples=[
            ("chunk-1", "doc-1", "Beta System approves requests. Audit Service stores approvals."),
            ("chunk-2", "doc-1", "Audit Service validates policy updates before publication."),
        ],
    )

    assert draft.status == "approved"
    assert draft.domain == "general"
    assert draft.tool_affinity_hints == ("retrieval.internal", "ontology.lookup")
    assert len(draft.evidence_links) >= 1

    active = service.get_active_draft("ws-1")
    assert active is not None
    assert active.draft_id == draft.draft_id


def test_ontology_service_process_build_reuses_architecture_draft_and_stamps_candidates() -> None:
    db = _database_manager()
    _seed_indexed_document(db)
    repo = OntologyRepository(db)
    architecture_service = OntologyArchitectureService(
        settings=_settings(),
        database_manager=db,
        ontology_repo=repo,
        model_config_service=_FakeModelResolver(),
    )
    extractor = _FakeExtractor()
    service = OntologyService(
        settings=_settings(),
        database_manager=db,
        task_dispatcher=_NoopTaskDispatcher(),
        graph_store=_NoopGraphStore(),
        ontology_extractor=extractor,
        ontology_architecture_service=architecture_service,
    )

    build = service.create_build(
        OntologyBuildCreateRequest(
            document_id="doc-1",
            workspace_id="ws-1",
            enqueue_processing=False,
        )
    )
    service.process_build(build.id)

    with db.session() as session:
        build_row = session.get(OntologyBuildORM, build.id)
        assert build_row is not None
        assert build_row.architecture_draft_id is not None
        assert build_row.domain == "policy_graph"

        entity_rows = session.scalars(select(OntologyCandidateEntityORM)).all()
        relation_rows = session.scalars(select(OntologyCandidateRelationORM)).all()

        assert len(entity_rows) == 1
        assert len(relation_rows) == 1
        assert entity_rows[0].architecture_draft_id == build_row.architecture_draft_id
        assert relation_rows[0].architecture_draft_id == build_row.architecture_draft_id
        assert entity_rows[0].provenance["architecture_draft_id"] == build_row.architecture_draft_id
        assert relation_rows[0].provenance["architecture_draft_id"] == build_row.architecture_draft_id

    assert extractor.seen_draft_id is not None
