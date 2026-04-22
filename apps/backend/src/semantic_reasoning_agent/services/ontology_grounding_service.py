from __future__ import annotations

from dataclasses import dataclass, field

from semantic_reasoning_agent.services.task_interpreter import TaskInterpretation


@dataclass(frozen=True)
class GroundingCandidate:
    value: str
    score: float
    source: str


@dataclass(frozen=True)
class OntologyGroundingResult:
    grounding_status: str
    candidates: tuple[GroundingCandidate, ...] = field(default_factory=tuple)
    selected: str | None = None


class OntologyGroundingService:
    def ground(self, prompt: str, interpretation: TaskInterpretation) -> OntologyGroundingResult:
        lowered = prompt.lower()
        candidates: list[GroundingCandidate] = []
        if interpretation.domain_guess:
            candidates.append(
                GroundingCandidate(value=interpretation.domain_guess, score=0.88, source="interpreter")
            )
        if "ontology" in lowered:
            candidates.append(GroundingCandidate(value="workspace_ontology", score=0.81, source="keyword"))
        if "graph" in lowered:
            candidates.append(GroundingCandidate(value="workspace_runtime_graph", score=0.82, source="keyword"))
        if not candidates:
            return OntologyGroundingResult(grounding_status="unmatched")
        if len(candidates) > 1:
            selected = max(candidates, key=lambda item: item.score).value
            return OntologyGroundingResult(
                grounding_status="ambiguous",
                candidates=tuple(sorted(candidates, key=lambda item: item.score, reverse=True)),
                selected=selected,
            )
        return OntologyGroundingResult(grounding_status="matched", candidates=tuple(candidates), selected=candidates[0].value)
