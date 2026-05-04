from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Sequence

from semantic_reasoning_agent.schemas.tasks import TaskResolveRequest


@dataclass(frozen=True)
class LoopStepTrace:
    tool_name: str
    status: str
    reason: str


@dataclass(frozen=True)
class AgenticLoopResult:
    traces: tuple[LoopStepTrace, ...] = field(default_factory=tuple)
    stop_reason: str = "completed"


class AgenticLoopService:
    def __init__(self) -> None:
        pass

    def validate_plan(self, plan: Sequence[Any], scope: Any) -> list[Any]:
        seen: set[str] = set()
        allowed = set(scope.allowed_tool_names)
        validated: list[Any] = []
        for step in plan:
            fingerprint = f"{step.tool_name}:{sorted(step.arguments.items())}"
            if step.tool_name not in allowed or fingerprint in seen:
                continue
            seen.add(fingerprint)
            validated.append(step)
        return validated

    @staticmethod
    def max_steps_for(request: TaskResolveRequest) -> int:
        if request.use_retrieval:
            return 4
        return 3
