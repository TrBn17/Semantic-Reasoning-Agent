from fastapi import APIRouter, Depends

from semantic_reasoning_agent.entrypoints.dependencies import get_model_config_service
from semantic_reasoning_agent.schemas.agents import TaskDefinition
from semantic_reasoning_agent.services.model_config_service import ModelConfigService
from .route_metadata import ADVANCED_ROUTE


router = APIRouter()


@router.get(
    "/tasks",
    response_model=list[TaskDefinition],
    summary="List internal task definitions",
    description="Advanced settings metadata. Internal task names remain supported but are no longer the primary frontend contract.",
    openapi_extra=ADVANCED_ROUTE,
)
def list_agent_tasks(
    model_config_service: ModelConfigService = Depends(get_model_config_service),
) -> list[TaskDefinition]:
    return model_config_service.list_tasks()
