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
    provider: str = "echo"
    model: str = "local-echo"


class ConversationResponse(BaseModel):
    id: str
    title: str
    provider: str
    model: str
    created_at: datetime
    updated_at: datetime
    messages: list[Message]


class SendMessageRequest(BaseModel):
    conversation_id: str
    content: str
    provider: str
    model: str
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
