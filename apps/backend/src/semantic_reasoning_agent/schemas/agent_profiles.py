from datetime import datetime, timezone

from pydantic import BaseModel, Field, model_validator

from semantic_reasoning_agent.schemas.agent_capabilities import (
    EvidencePolicySchema,
    ToolPolicySchema,
)
from semantic_reasoning_agent.schemas.agents import TaskType
from semantic_reasoning_agent.schemas.orchestration import (
    OrchestrationConfigSchema,
    default_orchestration_config,
)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class AgentProfileTaskModelAssignment(BaseModel):
    task_type: TaskType
    provider: str
    model: str


class AgentProfileToolAssignment(BaseModel):
    slot: str = "legacy"
    tool_name: str
    config_id: str | None = None
    enabled: bool = True
    position: int = 0

    @model_validator(mode="before")
    @classmethod
    def _coerce_legacy_shape(cls, value):  # noqa: ANN001
        if not isinstance(value, dict):
            return value
        tool_name = value.get("tool_name") or value.get("toolName") or ""
        slot = value.get("slot")
        if not slot:
            if tool_name == "supersearch.docs":
                slot = "rag"
            elif tool_name == "supersearch.graph":
                slot = "ontology_search"
            else:
                slot = "legacy"
        return {
            "slot": slot,
            "tool_name": tool_name,
            "config_id": value.get("config_id") or value.get("configId"),
            "enabled": value.get("enabled", value.get("is_enabled", True)),
            "position": value.get("position", 0),
        }


class AgentProfileResponse(BaseModel):
    id: str
    workspace_id: str
    name: str
    description: str
    system_prompt: str
    allow_chat_model_override: bool
    is_default: bool
    status: str
    capability_preset: str = "internal_qa"
    tool_policy: ToolPolicySchema = Field(default_factory=ToolPolicySchema)
    knowledge_pack_ids: list[str] = Field(default_factory=list)
    evidence_policy: EvidencePolicySchema = Field(default_factory=EvidencePolicySchema)
    orchestration_config: OrchestrationConfigSchema = Field(
        default_factory=default_orchestration_config
    )
    policy_config: dict = Field(default_factory=dict)
    task_models: list[AgentProfileTaskModelAssignment] = Field(default_factory=list)
    tool_assignments: list[AgentProfileToolAssignment] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class AgentProfileCreateRequest(BaseModel):
    workspace_id: str
    name: str
    description: str = ""
    system_prompt: str = ""
    allow_chat_model_override: bool = True
    is_default: bool = False
    status: str = "active"
    capability_preset: str = "internal_qa"
    tool_policy: ToolPolicySchema = Field(default_factory=ToolPolicySchema)
    knowledge_pack_ids: list[str] = Field(default_factory=list)
    evidence_policy: EvidencePolicySchema = Field(default_factory=EvidencePolicySchema)
    orchestration_config: OrchestrationConfigSchema = Field(
        default_factory=default_orchestration_config
    )
    policy_config: dict = Field(default_factory=dict)
    task_models: list[AgentProfileTaskModelAssignment] = Field(default_factory=list)
    tool_assignments: list[AgentProfileToolAssignment] = Field(default_factory=list)


class AgentProfileUpdateRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    system_prompt: str | None = None
    allow_chat_model_override: bool | None = None
    status: str | None = None
    capability_preset: str | None = None
    tool_policy: ToolPolicySchema | None = None
    knowledge_pack_ids: list[str] | None = None
    evidence_policy: EvidencePolicySchema | None = None
    orchestration_config: OrchestrationConfigSchema | None = None
    policy_config: dict | None = None
    task_models: list[AgentProfileTaskModelAssignment] | None = None
    tool_assignments: list[AgentProfileToolAssignment] | None = None
