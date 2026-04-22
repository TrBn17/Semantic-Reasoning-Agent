from __future__ import annotations

from dataclasses import dataclass

from semantic_reasoning_agent.services.conflict_engine import ConflictReport
from semantic_reasoning_agent.services.evidence_judge import SufficiencyResult


@dataclass(frozen=True)
class OutputRouteDecision:
    output_type: str
    grounded: bool
    reason: str


class OutputRouter:
    def route(self, sufficiency: SufficiencyResult, conflict: ConflictReport) -> OutputRouteDecision:
        if conflict.has_conflict:
            return OutputRouteDecision(output_type="needs_review", grounded=False, reason="conflicted_evidence")
        if sufficiency.state != "sufficient":
            return OutputRouteDecision(output_type="fallback_answer", grounded=False, reason=sufficiency.rationale)
        return OutputRouteDecision(output_type="answer", grounded=True, reason="grounded")
