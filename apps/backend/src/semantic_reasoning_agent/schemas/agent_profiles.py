from datetime import datetime, timezone

from pydantic import BaseModel, Field

from semantic_reasoning_agent.schemas.agents import TaskType


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class AgentProfileTaskModelAssignment(BaseModel):
    task_type: TaskType
    provider: str
    model: str


class AgentProfileToolAssignment(BaseModel):
    tool_name: str
    enabled: bool = True


class AgentProfileResponse(BaseModel):
    id: str
    workspace_id: str
    name: str
    description: str
    system_prompt: str
    allow_chat_model_override: bool
    is_default: bool
    status: str
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
    policy_config: dict = Field(default_factory=dict)
    task_models: list[AgentProfileTaskModelAssignment] = Field(default_factory=list)
    tool_assignments: list[AgentProfileToolAssignment] = Field(default_factory=list)


class AgentProfileUpdateRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    system_prompt: str | None = None
    allow_chat_model_override: bool | None = None
    status: str | None = None
    policy_config: dict | None = None
    task_models: list[AgentProfileTaskModelAssignment] | None = None
    tool_assignments: list[AgentProfileToolAssignment] | None = None
