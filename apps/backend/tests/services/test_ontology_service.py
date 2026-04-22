from io import BytesIO

import pytest
from docx import Document as DocxDocument

from semantic_reasoning_agent.schemas.ontology import OntologyBuildCreateRequest
from semantic_reasoning_agent.services.ontology_service import OntologyBuildError
from semantic_reasoning_agent.domain.ontology.models import OntologyNarrative
from semantic_reasoning_agent.schemas.ontology import (
    OntologyCandidateEntityUpdateRequest,
    OntologyDraftPublishRequest,
    OntologyGraphDraftNodeRequest,
    OntologyGraphDraftRelationRequest,
    OntologyReviewAction,
)


class _RateLimitedExtractor:
    def classify_document_domain(self, chunks) -> str:  # noqa: ANN001
        return "pending"

    def extract_ontology_candidates(  # noqa: ANN001
        self,
        chunks,
        workspace_id=None,
        provider=None,
        model=None,
    ):
        raise _FakeRateLimitError(
            "raw upstream error",
            body={
                "error": {
                    "message": "Provider returned error",
                    "metadata": {
                        "raw": (
                            "qwen/qwen3-next-80b-a3b-instruct:free is temporarily "
                            "rate-limited upstream. Please retry shortly."
                        )
                    },
                }
            },
        )

    def summarize_ontology(  # noqa: ANN001
        self,
        chunks,
        *,
        workspace_id=None,
        provider=None,
        model=None,
        domain=None,
    ) -> OntologyNarrative:
        return OntologyNarrative(title="Rate Limited Build", summary="Pending ontology summary.")


class _FakeRateLimitError(Exception):
    def __init__(self, message: str, *, body: dict) -> None:
        super().__init__(message)
        self.status_code = 429
        self.body = body


def test_process_build_marks_rate_limited_extraction_as_failed(
    document_service,
    ontology_service,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    document = document_service.upload_document(
        filename="ontology-source.docx",
        content=_build_docx_bytes(),
        content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )
    monkeypatch.setattr(
        ontology_service._task_dispatcher,
        "enqueue_ontology_build_processing",
        lambda build_id: None,
    )
    ontology_service._ontology_extractor = _RateLimitedExtractor()

    build = ontology_service.create_build(
        OntologyBuildCreateRequest(
            document_id=document.id,
            extraction_provider="openrouter",
            extraction_model="qwen/qwen3-next-80b-a3b-instruct:free",
        )
    )

    with pytest.raises(OntologyBuildError, match="upstream rate limit"):
        ontology_service.process_build(build.id)

    failed_build = ontology_service.get_build(build.id)
    assert failed_build.status.value == "failed"
    assert failed_build.domain is None
    assert "temporarily rate-limited upstream" in (failed_build.error_message or "")


def test_process_build_uses_extraction_domain_when_classification_is_deferred(
    document_service,
    ontology_service,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    document = document_service.upload_document(
        filename="ontology-source.docx",
        content=_build_docx_bytes(),
        content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )
    monkeypatch.setattr(
        ontology_service._task_dispatcher,
        "enqueue_ontology_build_processing",
        lambda build_id: None,
    )

    build = ontology_service.create_build(
        OntologyBuildCreateRequest(
            document_id=document.id,
            extraction_provider="echo",
            extraction_model="local-echo",
        )
    )
    ontology_service.process_build(build.id)

    completed_build = ontology_service.get_build(build.id)
    assert completed_build.status.value == "completed"
    assert completed_build.domain == "test_domain"
    assert completed_build.ontology_title == "Delivery Dependencies"
    assert completed_build.ontology_summary


def test_publish_build_appends_to_existing_version_and_keeps_document_title(
    document_service,
    ontology_service,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        ontology_service._task_dispatcher,
        "enqueue_ontology_build_processing",
        lambda build_id: None,
    )

    first_document = document_service.upload_document(
        filename="first.docx",
        content=_build_docx_bytes(),
        content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )
    first_build = ontology_service.create_build(
        OntologyBuildCreateRequest(
            document_id=first_document.id,
            extraction_provider="echo",
            extraction_model="local-echo",
        )
    )
    ontology_service.process_build(first_build.id)
    for entity in ontology_service.list_build_entities(first_build.id):
        ontology_service.review_entity(entity.id, action=OntologyReviewAction.approve)
    for relation in ontology_service.list_build_relations(first_build.id):
        ontology_service.review_relation(relation.id, action=OntologyReviewAction.approve)
    first_publish = ontology_service.publish_build(first_build.id)

    second_document = document_service.upload_document(
        filename="second.docx",
        content=_build_docx_bytes(),
        content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )
    second_build = ontology_service.create_build(
        OntologyBuildCreateRequest(
            document_id=second_document.id,
            extraction_provider="echo",
            extraction_model="local-echo",
        )
    )
    ontology_service.process_build(second_build.id)
    updated_candidate = ontology_service.list_build_entities(second_build.id)[0]
    ontology_service.update_entity(
        updated_candidate.id,
        OntologyCandidateEntityUpdateRequest(canonical_name="Alpha Initiative Prime"),
    )
    for entity in ontology_service.list_build_entities(second_build.id):
        ontology_service.review_entity(entity.id, action=OntologyReviewAction.approve)
    for relation in ontology_service.list_build_relations(second_build.id):
        ontology_service.review_relation(relation.id, action=OntologyReviewAction.approve)
    second_publish = ontology_service.publish_build(second_build.id)

    graph = ontology_service.get_graph()
    assert first_publish.version.version_number == 1
    assert second_publish.version.version_number == 2
    assert graph.version is not None
    assert graph.version.version_number == 2
    assert len(graph.entities) == 3
    assert any(entity.name == "Alpha Initiative Prime" for entity in graph.entities)
    reloaded_first_document = document_service.get_document(first_document.id)
    assert reloaded_first_document.title == first_document.title


def test_graph_draft_round_trip_publish_and_reset(
    document_service,
    ontology_service,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        ontology_service._task_dispatcher,
        "enqueue_ontology_build_processing",
        lambda build_id: None,
    )
    document = document_service.upload_document(
        filename="draft.docx",
        content=_build_docx_bytes(),
        content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )
    build = ontology_service.create_build(
        OntologyBuildCreateRequest(
            document_id=document.id,
            extraction_provider="echo",
            extraction_model="local-echo",
        )
    )
    ontology_service.process_build(build.id)
    for entity in ontology_service.list_build_entities(build.id):
        ontology_service.review_entity(entity.id, action=OntologyReviewAction.approve)
    for relation in ontology_service.list_build_relations(build.id):
        ontology_service.review_relation(relation.id, action=OntologyReviewAction.approve)
    ontology_service.publish_build(build.id)

    draft = ontology_service.create_draft_node(
        OntologyGraphDraftNodeRequest(name="Control Tower", entity_type="capability")
    )
    added_node = next(entity for entity in draft.entities if entity.name == "Control Tower")
    existing_node = draft.entities[0]
    draft = ontology_service.create_draft_relation(
        OntologyGraphDraftRelationRequest(
            source_entity_id=existing_node.id,
            target_entity_id=added_node.id,
            relation_type="monitors",
            evidence_text="Draft editor link.",
        )
    )
    assert draft.has_changes is True
    assert any(relation.relation_type == "monitors" for relation in draft.relations)

    preview = ontology_service.preview_publish(build.id)
    assert preview.diff_summary["entities_added"] >= 1
    assert preview.diff_summary["relations_added"] >= 1

    publish = ontology_service.publish_graph_draft(
        OntologyDraftPublishRequest(build_id=build.id)
    )
    assert publish.version.version_number == 2
    graph = ontology_service.get_graph()
    assert any(entity.name == "Control Tower" for entity in graph.entities)
    assert any(relation.relation_type == "monitors" for relation in graph.relations)

    reset = ontology_service.reset_graph_draft()
    assert reset.has_changes is False


def _build_docx_bytes() -> bytes:
    document = DocxDocument()
    document.add_heading("Delivery Plan", level=1)
    document.add_paragraph("Alpha initiative depends on the beta system for approvals.")
    document.add_paragraph("Beta system uses Audit service.")
    buffer = BytesIO()
    document.save(buffer)
    return buffer.getvalue()
