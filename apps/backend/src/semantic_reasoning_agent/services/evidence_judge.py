from __future__ import annotations

from dataclasses import dataclass

from semantic_reasoning_agent.services.context_assembler_service import ContextBundle


@dataclass(frozen=True)
class SufficiencyResult:
    state: str
    rationale: str


class EvidenceJudge:
    def evaluate(self, bundle: ContextBundle) -> SufficiencyResult:
        if bundle.citations or bundle.evidence:
            return SufficiencyResult(state="sufficient", rationale="grounded_evidence_available")
        return SufficiencyResult(state="insufficient", rationale="no_grounded_evidence")
