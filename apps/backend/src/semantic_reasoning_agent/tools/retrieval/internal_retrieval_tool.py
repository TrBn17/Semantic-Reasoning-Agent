from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from semantic_reasoning_agent.domain.contracts.evidence import (
    AnchorType,
    CitationAnchor,
    Evidence,
    Provenance,
)
from semantic_reasoning_agent.domain.contracts.tool_envelope import (
    ToolEnvelope,
    ToolMeta,
    ToolResult,
)
from semantic_reasoning_agent.domain.contracts.tool_spec import ToolSpec
from semantic_reasoning_agent.schemas.retrieval import Citation, RetrievalResult
from semantic_reasoning_agent.services.retrieval_service import RetrievalService
from semantic_reasoning_agent.tools.base import Tool


_SPEC_INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "query": {
            "type": "string",
            "description": "Natural-language question or search phrase.",
        },
        "document_ids": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Optional subset of workspace document IDs to search within.",
        },
        "top_k": {
            "type": "integer",
            "minimum": 1,
            "maximum": 20,
            "default": 5,
            "description": "Number of chunks to return, ranked by similarity.",
        },
    },
    "required": ["query"],
    "additionalProperties": False,
}


class InternalRetrievalTool(Tool):
    """Wraps ``RetrievalService.search`` as a §9 Tool.

    Returns one ``Evidence`` per ranked chunk, each carrying its citation
    anchor (page / section / sheet range) and full provenance pointing back
    to the document + tool call.
    """

    tool_name = "retrieval.internal"

    SPEC = ToolSpec(
        tool_name="retrieval.internal",
        tool_family="retrieval",
        tool_type="internal_service",
        version="1.0.0",
        description=(
            "Internal RAG over workspace-indexed document chunks. Returns "
            "ranked Evidence with citation anchors."
        ),
        input_schema=_SPEC_INPUT_SCHEMA,
        input_schema_ref="srag:retrieval.internal.in.v1",
        capabilities=("citation", "score"),
        risk_level="low",
        side_effect_level="read_only",
        supports_parallel=True,
        timeout_ms=15000,
    )

    def __init__(self, retrieval_service: RetrievalService) -> None:
        self._retrieval_service = retrieval_service

    def run(self, envelope: ToolEnvelope) -> ToolResult:
        arguments = envelope.arguments
        query = arguments.get("query") if isinstance(arguments, dict) else None
        if not isinstance(query, str) or not query.strip():
            raise ValueError("retrieval.internal requires a non-empty 'query' argument.")

        document_ids_raw = arguments.get("document_ids") if isinstance(arguments, dict) else None
        document_ids: list[str] | None = None
        if isinstance(document_ids_raw, list):
            document_ids = [str(item) for item in document_ids_raw if item]

        top_k = arguments.get("top_k") if isinstance(arguments, dict) else None
        if not isinstance(top_k, int) or top_k <= 0:
            top_k = min(envelope.constraints.max_results or 5, 10)

        search_response = self._retrieval_service.search(
            query=query,
            workspace_id=envelope.workspace_id,
            document_ids=document_ids,
            top_k=top_k,
        )

        now = datetime.now(timezone.utc)
        evidence = tuple(
            _result_to_evidence(result, envelope=envelope, captured_at=now)
            for result in search_response.results
        )
        return ToolResult(
            call_id=envelope.call_id,
            tool_name=self.tool_name,
            status="success" if evidence else "partial",
            started_at=now,
            finished_at=now,
            latency_ms=0,
            evidence=evidence,
            next_action_hints=(
                () if evidence else ("no_internal_match",)
            ),
            meta=ToolMeta(),
        )


def _result_to_evidence(
    result: RetrievalResult,
    *,
    envelope: ToolEnvelope,
    captured_at: datetime,
) -> Evidence:
    citation = result.citation
    anchor_type, locator = _anchor_from_citation(citation)
    return Evidence(
        evidence_id=uuid4(),
        source_type="internal_chunk",
        title=citation.document_title,
        content=citation.excerpt,
        citation_anchor=CitationAnchor(
            anchor_type=anchor_type,
            label=citation.location_label,
            locator=locator,
        ),
        provenance=Provenance(
            workspace_id=envelope.workspace_id,
            source_id=citation.document_id,
            tool_call_id=envelope.call_id,
            captured_at=captured_at,
        ),
        document_id=citation.document_id or None,
        chunk_id=citation.chunk_id or None,
        page=citation.page_number,
        section=citation.heading_path,
        sheet_name=citation.sheet_name,
        row_range=_format_row_range(citation),
        score=result.score,
        uri=citation.source_url or None,
    )


def _anchor_from_citation(citation: Citation) -> tuple[AnchorType, str]:
    if citation.document_type == "pdf" and citation.page_number is not None:
        return "page", str(citation.page_number)
    if citation.document_type == "docx" and citation.heading_path:
        return "section", citation.heading_path
    if citation.document_type == "xlsx" and citation.sheet_name and citation.row_start is not None and citation.row_end is not None:
        return "sheet_row", f"{citation.sheet_name}!{citation.row_start}:{citation.row_end}"
    if citation.document_type == "csv" and citation.row_start is not None and citation.row_end is not None:
        return "sheet_row", f"rows:{citation.row_start}-{citation.row_end}"
    return "section", citation.location_label or "document"


def _format_row_range(citation: Citation) -> str | None:
    if citation.row_start is None or citation.row_end is None:
        return None
    return f"{citation.row_start}-{citation.row_end}"
