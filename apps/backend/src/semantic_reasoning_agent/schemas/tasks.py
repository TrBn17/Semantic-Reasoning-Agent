from __future__ import annotations

from pydantic import BaseModel, Field

from semantic_reasoning_agent.core.runtime_constants import DEFAULT_TASK_TOP_K
from semantic_reasoning_agent.schemas.orchestration import OrchestrationMode
from semantic_reasoning_agent.schemas.retrieval import Citation
class TaskResolveRequest(BaseModel):
    content: str
    workspace_id: str | None = None
    conversation_id: str | None = None
    agent_profile_id: str | None = None
    provider: str | None = None
    model: str | None = None
    use_retrieval: bool = False
    document_ids: list[str] = Field(default_factory=list)
    top_k: int = DEFAULT_TASK_TOP_K
    enabled_tool_names: list[str] | None = None
    orchestration_mode: OrchestrationMode | None = None
    debug: bool = False


class TaskResolveResponse(BaseModel):
    task_id: str
    output_type: str = "answer"
    workflow_id: str | None = None
    orchestration_mode: OrchestrationMode = "legacy_static_plan"
    stop_reason: str | None = None
    grounded: bool = True
    content: str
    citations: list[Citation] = Field(default_factory=list)
    evidence: list[dict] = Field(default_factory=list)
    next_action_hints: list[str] = Field(default_factory=list)
    trace: list[dict] = Field(default_factory=list)
