from fastapi import APIRouter, Depends, Query

from semantic_reasoning_agent.entrypoints.dependencies import get_model_config_service
from semantic_reasoning_agent.schemas.settings import (
    PublicSettingsResponse,
    PublicSettingsUpdateRequest,
    SettingsModelOption,
)
from semantic_reasoning_agent.services.model_config_service import ModelConfigService

from .route_metadata import PUBLIC_ROUTE


router = APIRouter()


@router.get(
    "",
    response_model=PublicSettingsResponse,
    summary="Get frontend settings bootstrap",
    description=(
        "Canonical frontend bootstrap endpoint. Returns workspace summary, provider readiness, "
        "curated model catalog, and product-facing task defaults."
    ),
    openapi_extra=PUBLIC_ROUTE,
)
async def get_settings(
    workspace_id: str | None = Query(default=None),
    model_config_service: ModelConfigService = Depends(get_model_config_service),
) -> PublicSettingsResponse:
    return await model_config_service.get_public_settings(workspace_id)


@router.put(
    "",
    response_model=PublicSettingsResponse,
    summary="Update frontend settings",
    description=(
        "Canonical frontend settings write endpoint. Updates provider configuration and "
        "product-facing task defaults."
    ),
    openapi_extra=PUBLIC_ROUTE,
)
async def update_settings(
    payload: PublicSettingsUpdateRequest,
    model_config_service: ModelConfigService = Depends(get_model_config_service),
) -> PublicSettingsResponse:
    return await model_config_service.update_public_settings(payload)


@router.get(
    "/models",
    response_model=list[SettingsModelOption],
    summary="Get curated model catalog",
    description=(
        "Lightweight frontend-facing model catalog. Prefer this endpoint over provider discovery "
        "for normal settings and chat model selection flows."
    ),
    openapi_extra=PUBLIC_ROUTE,
)
async def list_settings_models(
    workspace_id: str | None = Query(default=None),
    model_config_service: ModelConfigService = Depends(get_model_config_service),
) -> list[SettingsModelOption]:
    return await model_config_service.list_public_models(workspace_id)
