import os
import sys
from pathlib import Path

import pytest

os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")
os.environ.setdefault("DATABASE_ECHO", "false")
os.environ.setdefault("CELERY_BROKER_URL", "memory://")
os.environ.setdefault("CELERY_RESULT_BACKEND", "cache+memory://")
os.environ.setdefault("CELERY_TASK_ALWAYS_EAGER", "true")
os.environ.setdefault("CELERY_TASK_EAGER_PROPAGATES", "true")
os.environ.setdefault("NEO4J_ENABLED", "false")


BACKEND_SRC = Path(__file__).resolve().parents[1] / "src"
if str(BACKEND_SRC) not in sys.path:
    sys.path.insert(0, str(BACKEND_SRC))

from semantic_reasoning_agent.entrypoints.dependencies import (  # noqa: E402
    get_document_service,
    get_ontology_service,
)
from semantic_reasoning_agent.core.container import get_app_container  # noqa: E402
from semantic_reasoning_agent.domain.ontology.models import (  # noqa: E402
    ExtractedEntity,
    ExtractedRelation,
    ExtractionResult,
)


class _StubOntologyExtractor:
    """Deterministic extractor for tests.

    Production uses `OpenDomainLLMExtractor` which calls Anthropic. Tests
    cannot depend on that, so this stub mirrors the structure the legacy
    rule extractor used to produce for the canonical test docx
    ("Alpha initiative depends on Beta system... Beta system uses Audit service.").
    Stubbed in conftest as autouse so phase-3 orchestration tests cover the
    review/publish pipeline without a real LLM call.
    """

    def classify_document_domain(self, chunks) -> str:  # noqa: ANN001
        return "test_domain"

    def extract_ontology_candidates(self, chunks, workspace_id=None) -> ExtractionResult:  # noqa: ANN001
        first_chunk_id = chunks[0].chunk_id if chunks else None
        provenance = {
            "extractor": "test_stub",
            "prompt_version": "v1",
            "run_id": "test-run",
            "source_chunk_id": first_chunk_id,
        }
        entities = [
            _stub_entity("Alpha Initiative", "alpha-initiative", first_chunk_id, provenance),
            _stub_entity("Beta System", "beta-system", first_chunk_id, provenance),
            _stub_entity("Audit Service", "audit-service", first_chunk_id, provenance),
        ]
        relations = [
            _stub_relation(
                source_key="alpha-initiative",
                target_key="beta-system",
                source_name="Alpha Initiative",
                target_name="Beta System",
                relation_type="depends_on",
                evidence_text="Alpha initiative depends on Beta system for approvals.",
                source_chunk_id=first_chunk_id,
                provenance=provenance,
            ),
            _stub_relation(
                source_key="beta-system",
                target_key="audit-service",
                source_name="Beta System",
                target_name="Audit Service",
                relation_type="uses",
                evidence_text="Beta system uses Audit service.",
                source_chunk_id=first_chunk_id,
                provenance=provenance,
            ),
        ]
        return ExtractionResult(domain="test_domain", entities=entities, relations=relations)


def _stub_entity(name: str, resolution_key: str, source_chunk_id, provenance: dict) -> ExtractedEntity:
    return ExtractedEntity(
        name=name,
        canonical_name=name,
        resolution_key=resolution_key,
        entity_type="test_thing",
        confidence=0.9,
        source_chunk_id=source_chunk_id,
        evidence_text=f"Mention of {name}",
        provenance=provenance,
        aliases=set(),
    )


def _stub_relation(
    *,
    source_key: str,
    target_key: str,
    source_name: str,
    target_name: str,
    relation_type: str,
    evidence_text: str,
    source_chunk_id,
    provenance: dict,
) -> ExtractedRelation:
    return ExtractedRelation(
        source_resolution_key=source_key,
        target_resolution_key=target_key,
        source_name=source_name,
        target_name=target_name,
        relation_type=relation_type,
        confidence=0.9,
        source_chunk_id=source_chunk_id,
        evidence_text=evidence_text,
        provenance=provenance,
    )


@pytest.fixture(autouse=True)
def reset_database() -> None:
    get_app_container().database_manager.reset_schema()


@pytest.fixture(autouse=True)
def stub_ontology_extractor() -> None:
    container = get_app_container()
    original = container.ontology_service._ontology_extractor
    container.ontology_service._ontology_extractor = _StubOntologyExtractor()
    try:
        yield
    finally:
        container.ontology_service._ontology_extractor = original


@pytest.fixture
def document_service():
    return get_document_service()


@pytest.fixture
def ontology_service():
    return get_ontology_service()
