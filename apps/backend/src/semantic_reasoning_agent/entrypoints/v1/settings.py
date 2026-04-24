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
        "Canonical frontend bootstrap endpoint. Returns workspace summary and "
        "provider readiness/configuration metadata."
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
        "Canonical frontend settings write endpoint. Updates provider configuration."
    ),
    openapi_extra=PUBLIC_ROUTE,
)
async def update_settings(
    payload: PublicSettingsUpdateRequest,
    model_config_service: ModelConfigService = Depends(get_model_config_service),
) -> PublicSettingsResponse:
    return await model_config_service.update_public_settings(payload)


@router.get(
    "/providers/{provider}/models",
    response_model=list[SettingsModelOption],
    summary="List provider models",
    description=(
        "Dynamic provider-specific model list for contextual model pickers."
    ),
    openapi_extra=PUBLIC_ROUTE,
)
async def list_settings_models_by_provider(
    provider: str,
    workspace_id: str | None = Query(default=None),
    model_config_service: ModelConfigService = Depends(get_model_config_service),
) -> list[SettingsModelOption]:
    models = await model_config_service.list_provider_models(provider=provider, workspace_id=workspace_id)
    return [
        SettingsModelOption(
            provider=provider,
            model=model.id,
            label=model.name or model.id,
            description=model.description or "",
            ready=model_config_service.is_ready(provider, model.id, workspace_id),
            reason="Ready to use."
            if model_config_service.is_ready(provider, model.id, workspace_id)
            else "Provider credentials or runtime adapter are not ready.",
            supports_streaming=model.supports_streaming,
            supports_structured_output=model.supports_structured_output,
            context_window=model.context_window,
            model_type=model.model_type,
            input_type=model.input_type,
            output_type=model.output_type,
        )
        for model in models
    ]


@router.get(
    "/models",
    response_model=list[SettingsModelOption],
    summary="Get model catalog (deprecated)",
    description="Compatibility endpoint. Prefer `/api/v1/settings/providers/{provider}/models`.",
    openapi_extra=PUBLIC_ROUTE,
)
async def list_settings_models(
    workspace_id: str | None = Query(default=None),
    model_config_service: ModelConfigService = Depends(get_model_config_service),
) -> list[SettingsModelOption]:
    return await model_config_service.list_public_models(workspace_id)
