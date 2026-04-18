from datetime import datetime, timezone
from uuid import uuid4

from pydantic import BaseModel, Field

from semantic_reasoning_agent.schemas.retrieval import Citation


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


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
    top_k: int = 3


class ChatReply(BaseModel):
    conversation: ConversationResponse
    reply: Message
    citations: list[Citation] = Field(default_factory=list)


class ModelOption(BaseModel):
    provider: str
    model: str
    ready: bool
    reason: str
