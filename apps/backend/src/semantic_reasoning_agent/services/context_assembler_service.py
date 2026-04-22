from __future__ import annotations

from dataclasses import dataclass, field

from semantic_reasoning_agent.schemas.retrieval import Citation
from semantic_reasoning_agent.schemas.tools import EvidenceSchema


@dataclass(frozen=True)
class ContextBundle:
    citations: tuple[Citation, ...] = field(default_factory=tuple)
    evidence: tuple[EvidenceSchema, ...] = field(default_factory=tuple)
    trace_notes: tuple[str, ...] = field(default_factory=tuple)


class ContextAssemblerService:
    def assemble(
        self,
        *,
        citations: list[Citation],
        evidence: list[EvidenceSchema],
    ) -> ContextBundle:
        dedup_citations: dict[str, Citation] = {}
        for citation in citations:
            key = f"{citation.document_id}:{citation.chunk_id}:{citation.location_label}"
            dedup_citations[key] = citation
        dedup_evidence: dict[str, EvidenceSchema] = {}
        for item in evidence:
            dedup_evidence[str(item.evidence_id)] = item
        notes = (
            f"citations={len(dedup_citations)}",
            f"evidence={len(dedup_evidence)}",
        )
        return ContextBundle(
            citations=tuple(dedup_citations.values()),
            evidence=tuple(dedup_evidence.values()),
            trace_notes=notes,
        )
