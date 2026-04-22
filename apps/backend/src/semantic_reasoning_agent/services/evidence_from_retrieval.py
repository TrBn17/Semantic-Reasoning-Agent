"""Map ``RetrievalResult`` rows into §9 ``Evidence`` — shared by internal retrieval + hybrid fusion."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from semantic_reasoning_agent.domain.contracts.evidence import (
    AnchorType,
    CitationAnchor,
    Evidence,
    Provenance,
)
from semantic_reasoning_agent.schemas.retrieval import Citation, RetrievalResult


@dataclass(frozen=True)
class _RetrievalEnvelopeStub:
    """Minimal stand-in for ``ToolEnvelope`` fields used by ``retrieval_result_to_evidence``."""

    workspace_id: str
    call_id: UUID


def retrieval_result_to_evidence(
    result: RetrievalResult,
    *,
    workspace_id: str,
    tool_call_id: UUID,
    captured_at: datetime,
) -> Evidence:
    envelope = _RetrievalEnvelopeStub(workspace_id=workspace_id, call_id=tool_call_id)
    return _result_to_evidence(result, envelope=envelope, captured_at=captured_at)


def _result_to_evidence(
    result: RetrievalResult,
    *,
    envelope: Any,
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
    if (
        citation.document_type == "xlsx"
        and citation.sheet_name
        and citation.row_start is not None
        and citation.row_end is not None
    ):
        return "sheet_row", f"{citation.sheet_name}!{citation.row_start}:{citation.row_end}"
    if citation.document_type == "csv" and citation.row_start is not None and citation.row_end is not None:
        return "sheet_row", f"rows:{citation.row_start}-{citation.row_end}"
    return "section", citation.location_label or "document"


def _format_row_range(citation: Citation) -> str | None:
    if citation.row_start is None or citation.row_end is None:
        return None
    return f"{citation.row_start}-{citation.row_end}"
