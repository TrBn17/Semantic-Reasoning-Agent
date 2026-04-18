from datetime import datetime, timezone
from uuid import uuid4

from semantic_reasoning_agent.domain.contracts import (
    CitationAnchor,
    Evidence,
    OntologyContext,
    ParsedChunk,
    ParsedDocument,
    ToolEnvelope,
    ToolResult,
)
from semantic_reasoning_agent.domain.errors import (
    DomainError,
    ExtractionError,
    ToolError,
    WorkflowError,
)


def test_tool_envelope_construct() -> None:
    env = ToolEnvelope(tool_id="ontology.extract_entities", inputs={"chunks": []})
    assert env.tool_id == "ontology.extract_entities"
    assert env.timeout_s == 60.0


def test_tool_result_construct() -> None:
    res = ToolResult(tool_id="x", status="ok", outputs={"entities": 0})
    assert res.status == "ok"
    assert res.error_code is None


def test_citation_and_evidence_construct() -> None:
    doc_id = uuid4()
    anchor = CitationAnchor(document_id=doc_id, page=3)
    ev = Evidence(
        evidence_id=uuid4(),
        kind="extraction",
        produced_by_tool="ontology.extract_entities",
        workflow_run_id=None,
        anchors=(anchor,),
        payload={"name": "Loan Product"},
        created_at=datetime.now(timezone.utc),
        confidence=0.82,
    )
    assert ev.anchors[0].document_id == doc_id
    assert ev.kind == "extraction"


def test_parsed_document_construct() -> None:
    chunk = ParsedChunk(ordinal=0, text="hello", page=1, char_start=0, char_end=5)
    pd = ParsedDocument(
        document_id=uuid4(),
        mime_type="application/pdf",
        chunks=(chunk,),
        extracted_text_length=5,
        parser_name="pypdf",
        parser_version="local-structured-v1",
        page_count=1,
    )
    assert pd.chunks[0].text == "hello"


def test_ontology_context_construct() -> None:
    ctx = OntologyContext(
        workspace_id=None,
        ontology_version_id=None,
        version_label=None,
        entity_types=("loan_product", "regulatory_clause"),
        relation_types=("governs", "issued_by"),
    )
    assert "loan_product" in ctx.entity_types
    assert ctx.is_frozen is False


def test_errors_inherit_domain_error() -> None:
    for cls in (ToolError, ExtractionError, WorkflowError):
        assert issubclass(cls, DomainError)
