from datetime import datetime
from uuid import uuid4

from pydantic import BaseModel, Field

from semantic_reasoning_agent.core.runtime_constants import DEFAULT_TASK_TOP_K
from semantic_reasoning_agent.schemas.orchestration import OrchestrationMode
from semantic_reasoning_agent.core.time import utc_now
from semantic_reasoning_agent.schemas.retrieval import Citation


class ConversationToolBinding(BaseModel):
    slot: str
    tool_name: str
    config_id: str | None = None
    label: str
    enabled: bool = True
    position: int = 0
    is_system: bool = False
    system_key: str | None = None


class Message(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    role: str
    content: str
    created_at: datetime = Field(default_factory=utc_now)


class ConversationCreateRequest(BaseModel):
    title: str
    workspace_id: str | None = None
    agent_profile_id: str | None = None
    provider: str | None = None
    model: str | None = None


class ConversationModelSelectionRequest(BaseModel):
    provider: str
    model: str
    workspace_id: str | None = None


class ConversationAgentProfileRequest(BaseModel):
    agent_profile_id: str | None = None
    workspace_id: str | None = None
    clear_model_override: bool = False


class ConversationResponse(BaseModel):
    id: str
    title: str
    workspace_id: str
    agent_profile_id: str | None = None
    provider: str
    model: str
    uses_model_override: bool = False
    effective_agent_name: str | None = None
    effective_tool_names: list[str] = Field(default_factory=list)
    effective_tool_bindings: list[ConversationToolBinding] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
    messages: list[Message]


class SendMessageRequest(BaseModel):
    conversation_id: str
    content: str
    provider: str | None = None
    model: str | None = None
    use_retrieval: bool = False
    workspace_id: str | None = None
    document_ids: list[str] = Field(default_factory=list)
    top_k: int = DEFAULT_TASK_TOP_K
    enabled_tool_names: list[str] | None = None
    orchestration_mode: OrchestrationMode | None = None


class ChatReply(BaseModel):
    conversation_id: str
    reply: Message
    orchestration_mode: OrchestrationMode = "legacy_static_plan"
    citations: list[Citation] = Field(default_factory=list)
    tool_calls: list[dict[str, str | int | None]] = Field(default_factory=list)


class ChatStreamEvent(BaseModel):
    event: str
    data: dict


class ModelOption(BaseModel):
    provider: str
    model: str
    ready: bool
    reason: str
