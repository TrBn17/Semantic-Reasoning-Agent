from fastapi import APIRouter, Depends

from semantic_reasoning_agent.api.dependencies import get_model_config_service
from semantic_reasoning_agent.schemas.chat import ModelOption
from semantic_reasoning_agent.services.model_config_service import ModelConfigService


router = APIRouter()


@router.get("", response_model=list[ModelOption])
def list_models(
    model_config_service: ModelConfigService = Depends(get_model_config_service),
) -> list[ModelOption]:
    return model_config_service.list_models()
