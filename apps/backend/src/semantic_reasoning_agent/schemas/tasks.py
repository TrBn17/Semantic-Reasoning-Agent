from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from semantic_reasoning_agent.schemas.retrieval import Citation
from semantic_reasoning_agent.schemas.tools import EvidenceSchema

TaskOutputClass = Literal[
    "answer",
    "ontology_candidates",
    "review_task",
    "graph_update_request",
    "promoted_evidence",
    "artifact",
]
TaskRunStatus = Literal["pending", "running", "completed", "failed"]
WorkflowMode = Literal["deterministic", "agentic"]


class TaskResolutionRequest(BaseModel):
    conversation_id: str | None = None
    entrypoint: str = "chat"
    content: str
    workspace_id: str | None = None
    task_type: str = "chat"
    requested_output: TaskOutputClass = "answer"
    provider: str | None = None
    model: str | None = None
    use_retrieval: bool = False
    document_ids: list[str] = Field(default_factory=list)
    top_k: int = 3
    web_enabled: bool = False
    freshness_required: bool = False


class ToolCallSummary(BaseModel):
    model_config = ConfigDict(frozen=True)

    tool_name: str
    status: str
    trace_id: str | None = None
    latency_ms: int = 0
    next_action_hints: list[str] = Field(default_factory=list)


class TaskResolutionResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    task_id: str
    workflow_run_id: str
    workflow_id: str
    workflow_mode: WorkflowMode
    status: TaskRunStatus
    output_type: TaskOutputClass
    reply: str | None = None
    citations: list[Citation] = Field(default_factory=list)
    evidence: list[EvidenceSchema] = Field(default_factory=list)
    tool_calls: list[ToolCallSummary] = Field(default_factory=list)
    trace_id: str | None = None
    provider: str | None = None
    model: str | None = None


class TaskRunRecord(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str
    workspace_id: str
    entrypoint: str
    task_type: str
    requested_output: TaskOutputClass
    status: TaskRunStatus
    workflow_id: str | None = None
    conversation_id: str | None = None
    provider: str | None = None
    model: str | None = None
    error_message: str | None = None
    created_at: datetime
    started_at: datetime | None = None
    finished_at: datetime | None = None
    updated_at: datetime
    output_payload: dict = Field(default_factory=dict)


class WorkflowSpecSchema(BaseModel):
    model_config = ConfigDict(frozen=True)

    workflow_id: str
    version: str
    mode: WorkflowMode
    description: str


class WorkflowRunRecord(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str
    task_id: str
    workflow_id: str
    workflow_version: str
    status: str
    created_at: datetime
    started_at: datetime | None = None
    finished_at: datetime | None = None
    output_payload: dict = Field(default_factory=dict)


class ToolCallRecord(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str
    task_id: str
    workflow_run_id: str | None = None
    call_id: str
    tool_name: str
    status: str
    trace_id: str | None = None
    provider: str | None = None
    provider_version: str | None = None
    latency_ms: int = 0
    error_code: str | None = None
    error_message: str | None = None
    created_at: datetime
    started_at: datetime | None = None
    finished_at: datetime | None = None
    input_payload: dict = Field(default_factory=dict)
    output_payload: dict = Field(default_factory=dict)
