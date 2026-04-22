from __future__ import annotations

from semantic_reasoning_agent.domain.contracts.evidence import AnchorType, Evidence
from semantic_reasoning_agent.schemas.retrieval import Citation
from semantic_reasoning_agent.schemas.tools import CitationAnchorSchema, EvidenceSchema, ProvenanceSchema


def citation_from_evidence(evidence: Evidence) -> Citation:
    document_type = infer_document_type(evidence)
    row_start, row_end = parse_row_range(evidence.row_range)
    return Citation(
        chunk_id=evidence.chunk_id or "",
        document_id=evidence.document_id or "",
        document_title=evidence.title,
        document_type=document_type,
        excerpt=evidence.content,
        location_label=evidence.citation_anchor.label,
        source_url=evidence.uri or "",
        page_number=evidence.page,
        heading_path=evidence.section,
        sheet_name=evidence.sheet_name,
        row_start=row_start,
        row_end=row_end,
    )


def evidence_to_schema(evidence: Evidence) -> EvidenceSchema:
    return EvidenceSchema(
        evidence_id=evidence.evidence_id,
        source_type=evidence.source_type,
        title=evidence.title,
        content=evidence.content,
        citation_anchor=CitationAnchorSchema(
            anchor_type=evidence.citation_anchor.anchor_type,
            label=evidence.citation_anchor.label,
            locator=evidence.citation_anchor.locator,
        ),
        provenance=ProvenanceSchema(
            workspace_id=evidence.provenance.workspace_id,
            captured_at=evidence.provenance.captured_at,
            source_id=evidence.provenance.source_id,
            tool_call_id=evidence.provenance.tool_call_id,
            parser_version=evidence.provenance.parser_version,
            extractor_version=evidence.provenance.extractor_version,
            model=evidence.provenance.model,
        ),
        summary=evidence.summary,
        uri=evidence.uri,
        document_id=evidence.document_id,
        chunk_id=evidence.chunk_id,
        page=evidence.page,
        section=evidence.section,
        sheet_name=evidence.sheet_name,
        row_range=evidence.row_range,
        entity_ids=list(evidence.entity_ids),
        relation_ids=list(evidence.relation_ids),
        score=evidence.score,
        trust_score=evidence.trust_score,
        freshness_ts=evidence.freshness_ts,
    )


def infer_document_type(evidence: Evidence) -> str:
    anchor_type: AnchorType = evidence.citation_anchor.anchor_type
    if evidence.page is not None or anchor_type == "page":
        return "pdf"
    if evidence.sheet_name or evidence.row_range or anchor_type == "sheet_row":
        return "xlsx"
    if evidence.section or anchor_type == "section":
        return "docx"
    return "document"


def parse_row_range(row_range: str | None) -> tuple[int | None, int | None]:
    if not row_range or "-" not in row_range:
        return None, None
    start, end = row_range.split("-", 1)
    try:
        return int(start), int(end)
    except ValueError:
        return None, None
