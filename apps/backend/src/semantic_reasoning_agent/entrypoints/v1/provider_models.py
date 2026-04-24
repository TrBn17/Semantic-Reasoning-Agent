"""
API routes for dynamic model discovery from provider APIs.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from semantic_reasoning_agent.entrypoints.dependencies import get_model_config_service
from semantic_reasoning_agent.services.model_config_service import ModelConfigService

from .route_metadata import INTERNAL_ROUTE


class DynamicModelResponse(BaseModel):
    """Model information returned from provider API."""

    id: str
    name: str | None = None
    context_window: int | None = None
    supports_streaming: bool = True
    supports_structured_output: bool = False
    description: str | None = None
    model_type: str | None = None
    input_type: str | None = None
    output_type: str | None = None


class ProviderModelsResponse(BaseModel):
    """Response containing models from a provider."""

    provider: str
    models: list[DynamicModelResponse]
    error: str | None = None


router = APIRouter(tags=["providers"])


@router.get(
    "/providers/{provider}/models",
    summary="Provider discovery by upstream provider",
    description="Advanced discovery/debug endpoint. Standard frontend flows should use `/api/v1/settings/models` instead.",
    openapi_extra=INTERNAL_ROUTE,
)
async def list_provider_models(
    provider: str,
    workspace_id: str | None = Query(default=None),
    model_config_service: ModelConfigService = Depends(get_model_config_service),
) -> ProviderModelsResponse:
    """
    Fetch available models directly from a provider's API.

    This endpoint dynamically queries the provider's API and returns the current list of available models.
    Useful when you want up-to-date models without manual configuration updates.

    **Supported providers:**
    - `openai`: Lists all available OpenAI models
    - `openrouter`: Lists all available OpenRouter models
    - `anthropic`: Lists all available Claude models
    - `gemini`: Lists all available Google Gemini models
    - `ollama`: Lists all models in local Ollama instance

    **Example:**
    ```
    GET /api/v1/providers/openai/models
    ```

    Returns:
    ```json
    {
      "provider": "openai",
      "models": [
        {
          "id": "gpt-4o",
          "name": "gpt-4o",
          "context_window": 128000,
          "supports_streaming": true,
          "supports_structured_output": true
        }
      ]
    }
    ```
    """
    try:
        models = await model_config_service.list_provider_models(provider.lower(), workspace_id)
        return ProviderModelsResponse(
            provider=provider,
            models=[
                DynamicModelResponse(
                    id=m.id,
                    name=m.name,
                    context_window=m.context_window,
                    supports_streaming=m.supports_streaming,
                    supports_structured_output=m.supports_structured_output,
                    description=m.description,
                    model_type=m.model_type,
                    input_type=m.input_type,
                    output_type=m.output_type,
                )
                for m in models
            ],
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/providers/models",
    summary="Provider discovery across providers",
    description="Advanced discovery/debug endpoint. Standard frontend flows should use `/api/v1/settings` or `/api/v1/settings/models` instead.",
    openapi_extra=INTERNAL_ROUTE,
)
async def list_all_provider_models(
    provider: str | None = Query(None),
    workspace_id: str | None = Query(default=None),
    model_config_service: ModelConfigService = Depends(get_model_config_service),
) -> dict[str, ProviderModelsResponse]:
    """
    Fetch available models from all or specific provider(s).

    If `provider` query param is specified, only that provider is queried.
    Otherwise, queries all configured providers.

    **Query Parameters:**
    - `provider` (optional): Specific provider to query (openai, openrouter, anthropic, gemini, ollama)

    **Example:**
    ```
    GET /api/v1/providers/models
    GET /api/v1/providers/models?provider=openai
    ```

    Returns:
    ```json
    {
      "openai": {
        "provider": "openai",
        "models": [...]
      },
      "anthropic": {
        "provider": "anthropic",
        "models": [...]
      }
    }
    ```
    """
    try:
        if provider:
            models = await model_config_service.list_provider_models(provider.lower(), workspace_id)
            return {
                provider: ProviderModelsResponse(
                    provider=provider,
                    models=[
                        DynamicModelResponse(
                            id=m.id,
                            name=m.name,
                            context_window=m.context_window,
                            supports_streaming=m.supports_streaming,
                            supports_structured_output=m.supports_structured_output,
                            description=m.description,
                            model_type=m.model_type,
                            input_type=m.input_type,
                            output_type=m.output_type,
                        )
                        for m in models
                    ],
                )
            }
        else:
            all_models = await model_config_service.list_all_provider_models(workspace_id)
            return {
                prov: ProviderModelsResponse(
                    provider=prov,
                    models=[
                        DynamicModelResponse(
                            id=m.id,
                            name=m.name,
                            context_window=m.context_window,
                            supports_streaming=m.supports_streaming,
                            supports_structured_output=m.supports_structured_output,
                            description=m.description,
                            model_type=m.model_type,
                            input_type=m.input_type,
                            output_type=m.output_type,
                        )
                        for m in models
                    ],
                )
                for prov, models in all_models.items()
            }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
