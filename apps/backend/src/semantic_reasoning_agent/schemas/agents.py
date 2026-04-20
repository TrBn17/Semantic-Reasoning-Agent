from typing import Literal

from pydantic import BaseModel, Field


TaskType = Literal[
    "chat",
    "retrieval",
    "ontology_extraction",
    "narrative_generation",
    "dashboard_generation",
]


class ModelOption(BaseModel):
    provider: str
    model: str
    label: str
    description: str
    ready: bool
    enabled: bool
    supports_runtime: bool
    supports_streaming: bool
    supports_structured_output: bool
    context_window: int | None = None
    recommended_for: list[TaskType] = Field(default_factory=list)
    required_env_fields: list[str] = Field(default_factory=list)
    missing_env_fields: list[str] = Field(default_factory=list)
    reason: str


class ProviderFieldDefinition(BaseModel):
    key: str
    label: str
    placeholder: str
    required: bool = True
    secret: bool = False
    help_text: str
    input_type: Literal["text", "select"] = "text"
    options: list[str] = Field(default_factory=list)


class ProviderFieldValue(BaseModel):
    key: str
    configured: bool = False
    source: Literal["database", "runtime", "missing"] = "missing"
    masked_value: str = ""


class ProviderConfigResponse(BaseModel):
    provider: str
    label: str
    enabled: bool
    supports_runtime: bool
    ready: bool
    reason: str
    fields: list[ProviderFieldDefinition]
    values: list[ProviderFieldValue]


class TaskDefinition(BaseModel):
    task_type: TaskType
    label: str
    description: str


class TaskAssignmentResponse(BaseModel):
    task_type: TaskType
    provider: str
    model: str
    ready: bool
    reason: str


class ProviderConfigUpdate(BaseModel):
    provider: str
    enabled: bool = True
    values: dict[str, str] = Field(default_factory=dict)


class TaskAssignmentUpdate(BaseModel):
    task_type: TaskType
    provider: str
    model: str


class AgentSettingsResponse(BaseModel):
    workspace_id: str
    models: list[ModelOption]
    providers: list[ProviderConfigResponse]
    tasks: list[TaskDefinition]
    task_assignments: list[TaskAssignmentResponse]


class AgentSettingsUpdateRequest(BaseModel):
    workspace_id: str
    providers: list[ProviderConfigUpdate] = Field(default_factory=list)
    task_assignments: list[TaskAssignmentUpdate] = Field(default_factory=list)
