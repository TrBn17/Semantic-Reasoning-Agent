"""
API routes for dynamic model discovery from provider APIs.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from semantic_reasoning_agent.entrypoints.dependencies import get_provider_models_service
from semantic_reasoning_agent.services.provider_models_service import ProviderModelsService


class DynamicModelResponse(BaseModel):
    """Model information returned from provider API."""

    id: str
    name: str | None = None
    context_window: int | None = None
    supports_streaming: bool = True
    supports_structured_output: bool = False
    description: str | None = None


class ProviderModelsResponse(BaseModel):
    """Response containing models from a provider."""

    provider: str
    models: list[DynamicModelResponse]
    error: str | None = None


router = APIRouter(tags=["providers"])


@router.get("/providers/{provider}/models")
async def list_provider_models(
    provider: str,
    service: ProviderModelsService = Depends(get_provider_models_service),
) -> ProviderModelsResponse:
    """
    Fetch available models directly from a provider's API.

    This endpoint dynamically queries the provider's API and returns the current list of available models.
    Useful when you want up-to-date models without manual configuration updates.

    **Supported providers:**
    - `openai`: Lists all available OpenAI models
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
        models = await service.get_provider_models(provider.lower())
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
                )
                for m in models
            ],
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/providers/models")
async def list_all_provider_models(
    provider: str | None = Query(None),
    service: ProviderModelsService = Depends(get_provider_models_service),
) -> dict[str, ProviderModelsResponse]:
    """
    Fetch available models from all or specific provider(s).

    If `provider` query param is specified, only that provider is queried.
    Otherwise, queries all configured providers.

    **Query Parameters:**
    - `provider` (optional): Specific provider to query (openai, anthropic, gemini, ollama)

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
            models = await service.get_provider_models(provider.lower())
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
                        )
                        for m in models
                    ],
                )
            }
        else:
            all_models = await service.get_all_provider_models()
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
