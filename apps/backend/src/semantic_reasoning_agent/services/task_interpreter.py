from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from semantic_reasoning_agent.core.runtime_constants import GRAPH_KEYWORDS, ONTOLOGY_KEYWORDS
from semantic_reasoning_agent.schemas.tasks import TaskResolveRequest

TaskIntent = Literal["lookup", "relationship", "summary", "action"]


@dataclass(frozen=True)
class TaskInterpretation:
    intent: TaskIntent
    output_type: str
    domain_guess: str | None
    freshness_required: bool
    sensitivity_level: str
    use_internal_only: bool
    candidate_workflow_type: str


class TaskInterpreter:
    def interpret(self, request: TaskResolveRequest) -> TaskInterpretation:
        prompt = request.content.lower()
        intent: TaskIntent = "summary"
        if any(keyword in prompt for keyword in GRAPH_KEYWORDS):
            intent = "relationship"
        elif any(keyword in prompt for keyword in ONTOLOGY_KEYWORDS):
            intent = "lookup"
        elif any(keyword in prompt for keyword in ("create", "generate", "run", "execute")):
            intent = "action"
        return TaskInterpretation(
            intent=intent,
            output_type="answer",
            domain_guess="knowledge_graph" if intent == "relationship" else None,
            freshness_required=any(word in prompt for word in ("latest", "newest", "today")),
            sensitivity_level="normal",
            use_internal_only=not any(word in prompt for word in ("web", "internet")),
            candidate_workflow_type="dynamic_agentic" if intent in {"relationship", "action"} else "grounded_qa",
        )
