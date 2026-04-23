"""Dynamic model fetching from provider APIs.

Each client calls the provider's live list endpoint:
  - OpenAI:    client.models.list()              -> GET /v1/models
  - Anthropic: client.models.list()              -> GET /v1/models
  - Gemini:    client.aio.models.list()          -> ListModels RPC
  - Ollama:    GET /api/tags                     -> local daemon catalog

No provider-specific hardcoded model catalogs are used; all models are fetched
live from provider APIs.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass

import aiohttp
import openai
from anthropic import Anthropic
from google import genai

from semantic_reasoning_agent.core.config import Settings, get_settings

@dataclass
class ProviderModel:
    """A single model entry returned from a provider catalog."""

    id: str
    name: str | None = None
    context_window: int | None = None
    supports_streaming: bool = True
    supports_structured_output: bool = False
    description: str | None = None


class OpenAIModelsClient:
    """Fetch models from OpenAI's /v1/models."""

    def __init__(self, api_key: str, base_url: str | None = None):
        kwargs: dict[str, str] = {"api_key": api_key}
        if base_url:
            kwargs["base_url"] = base_url
        self.client = openai.OpenAI(**kwargs)

    async def get_models(self) -> list[ProviderModel]:
        try:
            page = await asyncio.to_thread(self.client.models.list)
        except Exception as exc:
            raise RuntimeError(f"Failed to fetch OpenAI models: {exc}") from exc

        result: list[ProviderModel] = []
        for model in page.data:
            model_id = getattr(model, "id", None)
            if not model_id:
                continue
            result.append(
                ProviderModel(
                    id=model_id,
                    name=model_id,
                    context_window=None,
                    supports_streaming=True,
                    supports_structured_output=False,
                )
            )
        return sorted(result, key=lambda m: m.id, reverse=True)


class OpenRouterModelsClient:
    """Fetch models from OpenRouter's OpenAI-compatible /models endpoint."""

    def __init__(self, api_key: str, base_url: str):
        self.client = openai.OpenAI(api_key=api_key, base_url=base_url)

    async def get_models(self) -> list[ProviderModel]:
        try:
            page = await asyncio.to_thread(self.client.models.list)
        except Exception as exc:
            raise RuntimeError(f"Failed to fetch OpenRouter models: {exc}") from exc

        result: list[ProviderModel] = []
        for model in page.data:
            model_id = getattr(model, "id", "")
            if not model_id:
                continue
            result.append(
                ProviderModel(
                    id=model_id,
                    name=getattr(model, "name", None) or model_id,
                    context_window=None,
                    supports_streaming=True,
                    supports_structured_output=False,
                    description=getattr(model, "description", None),
                )
            )
        return sorted(result, key=lambda m: m.id)


class CloudflareModelsClient:
    """Fetch models from Cloudflare Workers AI model search endpoint."""

    def __init__(self, api_key: str, account_id: str):
        self.api_key = api_key
        self.account_id = account_id
        self.base_url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/models/search"

    @staticmethod
    def _is_chat_model(item: dict) -> bool:
        task = item.get("task") if isinstance(item, dict) else None
        if not isinstance(task, dict):
            return False
        task_name = str(task.get("name") or "").strip().lower()
        return task_name == "text generation"

    async def get_models(self) -> list[ProviderModel]:
        headers = {"Authorization": f"Bearer {self.api_key}"}
        page = 1
        per_page = 100
        result: list[ProviderModel] = []
        seen_model_ids: set[str] = set()

        try:
            async with aiohttp.ClientSession(headers=headers) as session:
                while True:
                    async with session.get(
                        self.base_url,
                        params={
                            "hide_experimental": "true",
                            "page": page,
                            "per_page": per_page,
                        },
                    ) as response:
                        if response.status != 200:
                            text = await response.text()
                            raise RuntimeError(
                                f"Cloudflare model search returned {response.status}: {text}"
                            )
                        payload = await response.json()

                    if not payload.get("success", False):
                        raise RuntimeError(
                            f"Cloudflare model search failed: {payload.get('errors') or payload.get('messages') or 'unknown error'}"
                        )

                    items = payload.get("result", [])
                    if not isinstance(items, list) or not items:
                        break

                    for item in items:
                        # Cloudflare chat/completions expects the model slug (e.g. @cf/...),
                        # not the UUID returned in `id`.
                        model_id = item.get("name")
                        if not self._is_chat_model(item):
                            continue
                        if not model_id or model_id in seen_model_ids:
                            continue
                        seen_model_ids.add(model_id)
                        result.append(
                            ProviderModel(
                                id=model_id,
                                name=item.get("name") or model_id,
                                context_window=item.get("context_window"),
                                supports_streaming=True,
                                supports_structured_output=False,
                                description=item.get("description"),
                            )
                        )

                    if len(items) < per_page:
                        break
                    page += 1
        except aiohttp.ClientError as exc:
            raise RuntimeError(f"Failed to fetch Cloudflare models: {exc}") from exc

        return sorted(result, key=lambda m: m.id)


class AnthropicModelsClient:
    """Fetch models from Anthropic's /v1/models (SDK: client.models.list)."""

    def __init__(self, api_key: str, base_url: str | None = None):
        kwargs: dict[str, str] = {"api_key": api_key}
        if base_url:
            kwargs["base_url"] = base_url
        self.client = Anthropic(**kwargs)

    async def get_models(self) -> list[ProviderModel]:
        try:
            page = await asyncio.to_thread(self.client.models.list)
        except Exception as exc:
            raise RuntimeError(f"Failed to fetch Anthropic models: {exc}") from exc

        result: list[ProviderModel] = []
        for model in page.data:
            model_id = getattr(model, "id", None)
            if not model_id:
                continue
            result.append(
                ProviderModel(
                    id=model_id,
                    name=getattr(model, "display_name", None) or model_id,
                    context_window=None,
                    supports_streaming=True,
                    supports_structured_output=True,
                )
            )
        return sorted(result, key=lambda m: m.id, reverse=True)


class GeminiModelsClient:
    """Fetch generative models from Google Gemini's ListModels RPC."""

    def __init__(self, api_key: str):
        self.client = genai.Client(api_key=api_key)

    async def get_models(self) -> list[ProviderModel]:
        try:
            pager = await self.client.aio.models.list()
        except Exception as exc:
            raise RuntimeError(f"Failed to fetch Gemini models: {exc}") from exc

        result: list[ProviderModel] = []
        try:
            async for model in pager:
                methods = getattr(model, "supported_actions", None) or getattr(
                    model, "supported_generation_methods", None
                )
                if methods and "generateContent" not in methods:
                    continue
                raw_name = getattr(model, "name", "") or ""
                model_id = raw_name.split("/", 1)[-1] if raw_name else ""
                if not model_id:
                    continue
                result.append(
                    ProviderModel(
                        id=model_id,
                        name=getattr(model, "display_name", None) or model_id,
                        context_window=None,
                        supports_streaming=True,
                        supports_structured_output=bool(
                            getattr(model, "supports_structured_output", False)
                        ),
                        description=getattr(model, "description", None),
                    )
                )
        except Exception as exc:
            raise RuntimeError(f"Failed to fetch Gemini models: {exc}") from exc

        return sorted(result, key=lambda m: m.id, reverse=True)


class OllamaModelsClient:
    """Fetch models from a local Ollama daemon."""

    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url.rstrip("/")

    async def get_models(self) -> list[ProviderModel]:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/api/tags") as response:
                    if response.status != 200:
                        raise RuntimeError(
                            f"Ollama server returned status {response.status}"
                        )
                    payload = await response.json()
        except aiohttp.ClientError as exc:
            raise RuntimeError(f"Failed to reach Ollama at {self.base_url}: {exc}") from exc

        result: list[ProviderModel] = []
        for model_info in payload.get("models", []):
            model_name = model_info.get("name", "")
            if not model_name:
                continue
            result.append(
                ProviderModel(
                    id=model_name,
                    name=model_name,
                    context_window=None,
                    supports_streaming=True,
                    supports_structured_output=False,
                )
            )
        return sorted(result, key=lambda m: m.id)


class ProviderModelsService:
    """Composes per-provider clients and fetches catalogs concurrently."""

    PROVIDERS: tuple[str, ...] = (
        "openai",
        "openrouter",
        "cloudflare",
        "anthropic",
        "gemini",
        "ollama",
    )

    def __init__(self, settings: Settings | None = None):
        self._settings = settings or get_settings()

    async def get_provider_models(
        self,
        provider: str,
        *,
        api_key: str | None = None,
        base_url: str | None = None,
    ) -> list[ProviderModel]:
        """Fetch the catalog for a single provider.

        Raises ValueError if the provider is unknown or credentials are missing.
        Raises RuntimeError if the upstream API call fails.
        """
        if provider == "openai":
            resolved_api_key = api_key or self._settings.openai_api_key
            resolved_base_url = base_url or self._settings.openai_base_url
            if not resolved_api_key:
                raise ValueError("OpenAI API key not configured")
            return await OpenAIModelsClient(resolved_api_key, resolved_base_url).get_models()

        if provider == "openrouter":
            resolved_api_key = api_key or self._settings.openrouter_api_key
            resolved_base_url = base_url or self._settings.openrouter_base_url
            if not resolved_api_key:
                raise ValueError("OpenRouter API key not configured")
            return await OpenRouterModelsClient(resolved_api_key, resolved_base_url).get_models()

        if provider == "cloudflare":
            resolved_api_key = api_key or self._settings.cloudflare_api_key
            resolved_base_url = base_url or (
                f"https://api.cloudflare.com/client/v4/accounts/{self._settings.cloudflare_account_id}/ai/v1"
                if self._settings.cloudflare_account_id
                else None
            )
            if not resolved_api_key:
                raise ValueError("Cloudflare API key not configured")
            if not resolved_base_url:
                raise ValueError("Cloudflare account id not configured")
            marker = "/accounts/"
            if marker not in resolved_base_url:
                raise ValueError("Cloudflare base URL is invalid")
            account_id = resolved_base_url.split(marker, 1)[1].split("/", 1)[0]
            if not account_id:
                raise ValueError("Cloudflare account id not configured")
            return await CloudflareModelsClient(resolved_api_key, account_id).get_models()

        if provider == "anthropic":
            resolved_api_key = api_key or self._settings.anthropic_api_key
            resolved_base_url = base_url or self._settings.anthropic_base_url
            if not resolved_api_key:
                raise ValueError("Anthropic API key not configured")
            return await AnthropicModelsClient(
                resolved_api_key,
                resolved_base_url,
            ).get_models()

        if provider == "gemini":
            resolved_api_key = api_key or self._settings.google_api_key
            if not resolved_api_key:
                raise ValueError("Google API key not configured")
            return await GeminiModelsClient(resolved_api_key).get_models()

        if provider == "ollama":
            resolved_base_url = (
                base_url
                or self._settings.ollama_base_url
                or "http://localhost:11434"
            )
            return await OllamaModelsClient(resolved_base_url).get_models()

        raise ValueError(f"Unsupported provider: {provider}")

    async def get_all_provider_models(
        self,
        credentials: dict[str, dict[str, str | None]] | None = None,
    ) -> dict[str, list[ProviderModel]]:
        """Fetch every supported provider's catalog in parallel.

        Providers that aren't configured or whose upstream call fails yield `[]`.
        """
        tasks = [
            self.get_provider_models(
                provider,
                api_key=(credentials or {}).get(provider, {}).get("api_key"),
                base_url=(credentials or {}).get(provider, {}).get("base_url"),
            )
            for provider in self.PROVIDERS
        ]
        settled = await asyncio.gather(*tasks, return_exceptions=True)

        results: dict[str, list[ProviderModel]] = {}
        for provider, outcome in zip(self.PROVIDERS, settled, strict=True):
            if isinstance(outcome, Exception):
                # Expected when credentials absent or upstream unreachable.
                results[provider] = []
                continue
            results[provider] = outcome
        return results


