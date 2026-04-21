from datetime import datetime, timezone
from uuid import uuid4

from semantic_reasoning_agent.domain.contracts import (
    CitationAnchor,
    Evidence,
    OntologyContext,
    OntologyContextRef,
    Provenance,
    ToolConstraints,
    ToolEnvelope,
    ToolMeta,
    ToolResult,
    ToolSpec,
)
from semantic_reasoning_agent.documents.models import ParsedChunk, ParsedDocument
from semantic_reasoning_agent.domain.errors import (
    DomainError,
    ExtractionError,
    ToolError,
    WorkflowError,
)
from semantic_reasoning_agent.domain.ontology.models import OntologySourceChunk


def test_tool_envelope_construct() -> None:
    env = ToolEnvelope(
        call_id=uuid4(),
        tool_name="ontology.extract_entities",
        workspace_id="workspace-demo",
        task_id=str(uuid4()),
        task_type="chat.retrieve",
        arguments={"chunks": []},
    )
    assert env.tool_name == "ontology.extract_entities"
    assert env.constraints.timeout_ms == 15000
    assert env.ontology_context.entity_hints == ()


def test_tool_result_construct() -> None:
    now = datetime.now(timezone.utc)
    call_id = uuid4()
    res = ToolResult(
        call_id=call_id,
        tool_name="x",
        status="success",
        started_at=now,
        finished_at=now,
        latency_ms=0,
    )
    assert res.status == "success"
    assert res.error_code is None
    assert res.evidence == ()
    assert res.meta.provider is None


def test_citation_and_evidence_construct() -> None:
    workspace_id = "workspace-demo"
    doc_id = str(uuid4())
    anchor = CitationAnchor(anchor_type="page", label="page 3", locator="3")
    provenance = Provenance(
        workspace_id=workspace_id,
        captured_at=datetime.now(timezone.utc),
        tool_call_id=uuid4(),
    )
    ev = Evidence(
        evidence_id=uuid4(),
        source_type="internal_chunk",
        title="Loan Product Handbook",
        content="Term loans must be disbursed within 10 business days.",
        citation_anchor=anchor,
        provenance=provenance,
        document_id=doc_id,
        page=3,
        score=0.82,
    )
    assert ev.citation_anchor.anchor_type == "page"
    assert ev.source_type == "internal_chunk"
    assert ev.document_id == doc_id
    assert ev.provenance.workspace_id == workspace_id


def test_parsed_document_construct() -> None:
    chunk = ParsedChunk(text="hello", chunk_index=0, page_number=1)
    pd = ParsedDocument(
        document_type="pdf",
        title="hello",
        chunks=(chunk,),
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


def test_ontology_context_ref_defaults() -> None:
    ref = OntologyContextRef()
    assert ref.domain is None
    assert ref.entity_hints == ()
    assert ref.relation_hints == ()
    assert ref.normalization_rules == ()


def test_tool_constraints_defaults() -> None:
    c = ToolConstraints()
    assert c.web_enabled is False
    assert c.freshness_required is False
    assert c.max_results == 10
    assert c.timeout_ms == 15000


def test_tool_spec_serialization() -> None:
    schema: dict = {
        "type": "object",
        "properties": {"query": {"type": "string"}},
        "required": ["query"],
    }
    spec = ToolSpec(
        tool_name="retrieval.internal",
        tool_family="retrieval",
        tool_type="internal_service",
        version="1.0.0",
        description="Internal RAG over workspace chunks.",
        input_schema=schema,
        input_schema_ref="srag:retrieval.internal.in.v1",
        capabilities=("citation", "score"),
    )
    anthropic = spec.to_anthropic_tool()
    assert anthropic["name"] == "retrieval.internal"
    assert anthropic["input_schema"]["required"] == ["query"]

    openai = spec.to_openai_tool()
    assert openai["type"] == "function"
    assert openai["function"]["name"] == "retrieval.internal"
    assert openai["function"]["parameters"]["required"] == ["query"]


def test_tool_meta_default() -> None:
    meta = ToolMeta()
    assert meta.provider is None
    assert meta.trace_id is None


def test_errors_inherit_domain_error() -> None:
    for cls in (ToolError, ExtractionError, WorkflowError):
        assert issubclass(cls, DomainError)


def test_ontology_source_chunk_construct() -> None:
    chunk = OntologySourceChunk(chunk_id="chunk-1", text="domain text")
    assert chunk.chunk_id == "chunk-1"
    assert chunk.text == "domain text"
