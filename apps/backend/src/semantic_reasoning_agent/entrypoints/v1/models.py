from fastapi import APIRouter, Depends, Query

from semantic_reasoning_agent.entrypoints.dependencies import get_model_config_service
from semantic_reasoning_agent.schemas.agents import ModelOption
from semantic_reasoning_agent.services.model_config_service import ModelConfigService


router = APIRouter()


@router.get("", response_model=list[ModelOption])
async def list_models(
    workspace_id: str | None = Query(default=None),
    model_config_service: ModelConfigService = Depends(get_model_config_service),
) -> list[ModelOption]:
    return await model_config_service.list_models(workspace_id)
