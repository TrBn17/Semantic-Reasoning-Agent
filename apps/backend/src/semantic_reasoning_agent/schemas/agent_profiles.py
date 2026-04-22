from datetime import datetime, timezone

from pydantic import BaseModel, Field

from semantic_reasoning_agent.schemas.agent_capabilities import (
    EvidencePolicySchema,
    ToolPolicySchema,
)
from semantic_reasoning_agent.schemas.agents import TaskType


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class AgentProfileTaskModelAssignment(BaseModel):
    task_type: TaskType
    provider: str
    model: str


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
    policy_config: dict = Field(default_factory=dict)
    task_models: list[AgentProfileTaskModelAssignment] = Field(default_factory=list)
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
    policy_config: dict = Field(default_factory=dict)
    task_models: list[AgentProfileTaskModelAssignment] = Field(default_factory=list)


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
    policy_config: dict | None = None
    task_models: list[AgentProfileTaskModelAssignment] | None = None
