from __future__ import annotations

from pydantic import BaseModel, Field

from semantic_reasoning_agent.schemas.retrieval import Citation
from semantic_reasoning_agent.schemas.tools import EvidenceSchema


class TaskResolveRequest(BaseModel):
    content: str
    workspace_id: str | None = None
    conversation_id: str | None = None
    agent_profile_id: str | None = None
    provider: str | None = None
    model: str | None = None
    use_retrieval: bool = False
    document_ids: list[str] = Field(default_factory=list)
    top_k: int = 3


class TaskResolveResponse(BaseModel):
    task_id: str
    workflow_id: str
    output_type: str = "answer"
    content: str
    citations: list[Citation] = Field(default_factory=list)
    evidence: list[EvidenceSchema] = Field(default_factory=list)
    next_action_hints: list[str] = Field(default_factory=list)
