from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

OrchestrationMode = Literal["legacy_static_plan", "react_two_agent"]


class StopPolicySchema(BaseModel):
    max_iterations: int = Field(default=4, ge=1, le=12)


class OrchestratorSchema(BaseModel):
    strategy: Literal["legacy_static_plan", "react_two_agent"] = "legacy_static_plan"
    enabled: bool = True


class OrchestrationConfigSchema(BaseModel):
    version: str = "1.0"
    mode: OrchestrationMode = Field(
        default="legacy_static_plan",
        description=(
            "legacy_static_plan: deterministic tool ordering. "
            "react_two_agent: LlamaIndex ReAct orchestrator delegating to built-in Graphiti + "
            "document specialists (agents-as-tools; SKILLS/MEMORY from packaged files + workspace DB)."
        ),
    )
    orchestrator: OrchestratorSchema = Field(default_factory=OrchestratorSchema)
    stop_policy: StopPolicySchema = Field(default_factory=StopPolicySchema)


def default_orchestration_config() -> OrchestrationConfigSchema:
    return OrchestrationConfigSchema()

