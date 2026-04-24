from typing import Literal

from pydantic import BaseModel, Field

from semantic_reasoning_agent.schemas.agents import ProviderConfigUpdate, ProviderFieldDefinition
from semantic_reasoning_agent.schemas.auth import WorkspaceSummary


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
    model_type: str | None = None
    input_type: str | None = None
    output_type: str | None = None


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


class WorkspaceSearchDefaultsResponse(BaseModel):
    embedding_provider: str
    embedding_model: str
    ready: bool
    reason: str


class PublicSettingsResponse(BaseModel):
    workspace: WorkspaceSummary
    providers: list[SettingsProviderResponse]
    search_defaults: WorkspaceSearchDefaultsResponse


class WorkspaceSearchDefaultsUpdateRequest(BaseModel):
    embedding_provider: str
    embedding_model: str


class PublicSettingsUpdateRequest(BaseModel):
    workspace_id: str
    providers: list[ProviderConfigUpdate] = Field(default_factory=list)
    search_defaults: WorkspaceSearchDefaultsUpdateRequest | None = None
