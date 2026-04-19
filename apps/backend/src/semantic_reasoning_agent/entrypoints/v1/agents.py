from fastapi import APIRouter, Depends, Query

from semantic_reasoning_agent.entrypoints.dependencies import get_model_config_service
from semantic_reasoning_agent.schemas.agents import (
    AgentSettingsResponse,
    AgentSettingsUpdateRequest,
    ModelOption,
    TaskDefinition,
)
from semantic_reasoning_agent.services.model_config_service import ModelConfigService


router = APIRouter()


@router.get("/settings", response_model=AgentSettingsResponse)
def get_agent_settings(
    workspace_id: str | None = Query(default=None),
    model_config_service: ModelConfigService = Depends(get_model_config_service),
) -> AgentSettingsResponse:
    return model_config_service.get_agent_settings(workspace_id)


@router.get("/tasks", response_model=list[TaskDefinition])
def list_agent_tasks(
    model_config_service: ModelConfigService = Depends(get_model_config_service),
) -> list[TaskDefinition]:
    return model_config_service.list_tasks()


@router.get("/catalog", response_model=list[ModelOption])
def get_agent_catalog(
    workspace_id: str | None = Query(default=None),
    model_config_service: ModelConfigService = Depends(get_model_config_service),
) -> list[ModelOption]:
    return model_config_service.get_catalog(workspace_id)


@router.put("/settings", response_model=AgentSettingsResponse)
def update_agent_settings(
    payload: AgentSettingsUpdateRequest,
    model_config_service: ModelConfigService = Depends(get_model_config_service),
) -> AgentSettingsResponse:
    return model_config_service.update_agent_settings(payload)
