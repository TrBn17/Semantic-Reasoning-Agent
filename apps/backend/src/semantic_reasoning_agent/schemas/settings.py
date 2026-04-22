from typing import Literal

from pydantic import BaseModel, Field

from semantic_reasoning_agent.schemas.agents import (
    ProviderConfigUpdate,
    ProviderFieldDefinition,
    TaskType,
)
from semantic_reasoning_agent.schemas.auth import WorkspaceSummary


SettingsUseCase = Literal[
    "chat_default",
    "retrieval_answer_default",
    "ontology_extraction_default",
    "narrative_default",
    "dashboard_default",
]


class SettingsModelOption(BaseModel):
    provider: str
    model: str
    label: str
    description: str
    ready: bool
    reason: str
    supports_streaming: bool
    supports_structured_output: bool
    context_window: int | None = None


class SettingsProviderFieldValue(BaseModel):
    key: str
    configured: bool = False
    source: Literal["database", "runtime", "missing"] = "missing"
    display_value: str = ""


class SettingsProviderResponse(BaseModel):
    provider: str
    label: str
    enabled: bool
    ready: bool
    status_text: str
    fields: list[ProviderFieldDefinition]
    values: list[SettingsProviderFieldValue]


class TaskDefaultResponse(BaseModel):
    use_case: SettingsUseCase
    task_type: TaskType
    label: str
    description: str
    provider: str
    model: str
    ready: bool
    reason: str


class TaskDefaultUpdate(BaseModel):
    use_case: SettingsUseCase
    provider: str
    model: str


class PublicSettingsResponse(BaseModel):
    workspace: WorkspaceSummary
    providers: list[SettingsProviderResponse]
    model_catalog: list[SettingsModelOption]
    task_defaults: list[TaskDefaultResponse]
    preferred_default_chat_model: SettingsModelOption | None = None


class PublicSettingsUpdateRequest(BaseModel):
    workspace_id: str
    providers: list[ProviderConfigUpdate] = Field(default_factory=list)
    task_defaults: list[TaskDefaultUpdate] = Field(default_factory=list)
