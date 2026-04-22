from datetime import datetime, timezone

from pydantic import BaseModel, Field


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class KnowledgePackResponse(BaseModel):
    id: str
    workspace_id: str
    name: str
    description: str = ""
    document_ids: list[str] = Field(default_factory=list)
    status: str = "active"
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class KnowledgePackCreateRequest(BaseModel):
    workspace_id: str
    name: str
    description: str = ""
    document_ids: list[str] = Field(default_factory=list)
    status: str = "active"


class KnowledgePackUpdateRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    document_ids: list[str] | None = None
    status: str | None = None
