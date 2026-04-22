"""Dynamic model fetching from provider APIs.

Each client calls the provider's live list endpoint:
  - OpenAI:    client.models.list()              -> GET /v1/models
  - Anthropic: client.models.list()              -> GET /v1/models
  - Gemini:    client.aio.models.list()          -> ListModels RPC
  - Ollama:    GET /api/tags                     -> local daemon catalog

Maintained fallbacks are kept for providers where the live list endpoint is
unavailable or unreliable from development/test environments.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any

import aiohttp
import openai
from anthropic import Anthropic
from google import genai

from semantic_reasoning_agent.core.config import Settings, get_settings

CHAT_MODEL_PREFIXES: tuple[str, ...] = ("gpt-", "chatgpt-", "o1", "o3", "o4")
NON_CHAT_MODEL_MARKERS: tuple[str, ...] = (
    "embedding",
    "whisper",
    "dall-e",
    "tts",
    "audio",
    "moderation",
    "image",
    "realtime",
    "transcribe",
)
ANTHROPIC_MAINTAINED_MODELS: tuple[tuple[str, str, int], ...] = (
    ("claude-opus-4-0", "Claude Opus 4.0", 200_000),
    ("claude-sonnet-4-5", "Claude Sonnet 4.5", 200_000),
)
OPENAI_MAINTAINED_MODELS: tuple[tuple[str, str, int], ...] = (
    ("gpt-5-mini", "GPT-5 Mini", 128_000),
    ("gpt-4o-mini", "GPT-4o Mini", 128_000),
)
OPENROUTER_MAINTAINED_MODELS: tuple[tuple[str, str, int | None], ...] = (
    (
        "nvidia/nemotron-3-super-120b-a12b:free",
        "NVIDIA Nemotron-3 Super 120B A12B",
        None,
    ),
)


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
    """Fetch chat-capable models from OpenAI's /v1/models."""

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
            if not _is_openai_chat_model(model.id):
                continue
            result.append(
                ProviderModel(
                    id=model.id,
                    name=model.id,
                    context_window=_infer_openai_context_window(model.id),
                    supports_streaming=True,
                    supports_structured_output=model.id.startswith(("gpt-4", "o1", "o3", "o4")),
                )
            )
        return sorted(result, key=lambda m: m.id, reverse=True)


class OpenRouterModelsClient:
    """Fetch chat-capable models from OpenRouter's OpenAI-compatible /models endpoint."""

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
            if not model_id or not _is_openrouter_chat_model(model_id):
                continue
            result.append(
                ProviderModel(
                    id=model_id,
                    name=getattr(model, "name", None) or model_id,
                    context_window=None,
                    supports_streaming=True,
                    supports_structured_output=True,
                    description=getattr(model, "description", None),
                )
            )
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
                        context_window=_extract_gemini_context_window(model),
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
                    context_window=_infer_ollama_context_window(model_name),
                    supports_streaming=True,
                    supports_structured_output=False,
                )
            )
        return sorted(result, key=lambda m: m.id)


class ProviderModelsService:
    """Composes per-provider clients and fetches catalogs concurrently."""

    PROVIDERS: tuple[str, ...] = ("openai", "openrouter", "anthropic", "gemini", "ollama")

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
            try:
                return await OpenAIModelsClient(resolved_api_key, resolved_base_url).get_models()
            except RuntimeError:
                return _openai_maintained_catalog()

        if provider == "openrouter":
            resolved_api_key = api_key or self._settings.openrouter_api_key
            resolved_base_url = base_url or self._settings.openrouter_base_url
            if not resolved_api_key:
                raise ValueError("OpenRouter API key not configured")
            try:
                return await OpenRouterModelsClient(resolved_api_key, resolved_base_url).get_models()
            except RuntimeError:
                return _openrouter_maintained_catalog()

        if provider == "anthropic":
            resolved_api_key = api_key or self._settings.anthropic_api_key
            resolved_base_url = base_url or self._settings.anthropic_base_url
            if not resolved_api_key:
                raise ValueError("Anthropic API key not configured")
            try:
                return await AnthropicModelsClient(
                    resolved_api_key,
                    resolved_base_url,
                ).get_models()
            except RuntimeError:
                # Anthropic-compatible gateways often omit /v1/models.
                return _anthropic_maintained_catalog()

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


def _is_openai_chat_model(model_id: str) -> bool:
    lower = model_id.lower()
    if any(marker in lower for marker in NON_CHAT_MODEL_MARKERS):
        return False
    return any(lower.startswith(prefix) for prefix in CHAT_MODEL_PREFIXES)


def _infer_openai_context_window(model_id: str) -> int | None:
    lower = model_id.lower()
    mapping = (
        ("o4", 200_000),
        ("o3", 200_000),
        ("o1", 128_000),
        ("gpt-4.1", 1_000_000),
        ("gpt-4o", 128_000),
        ("gpt-4-turbo", 128_000),
        ("gpt-4", 8_192),
        ("gpt-3.5", 16_384),
    )
    for key, window in mapping:
        if key in lower:
            return window
    return None


def _is_openrouter_chat_model(model_id: str) -> bool:
    lower = model_id.lower()
    return not any(marker in lower for marker in NON_CHAT_MODEL_MARKERS)


def _extract_gemini_context_window(model: Any) -> int | None:
    for attr in ("input_token_limit", "inputTokenLimit"):
        value = getattr(model, attr, None)
        if isinstance(value, int) and value > 0:
            return value
    name = (getattr(model, "name", "") or "").lower()
    if "gemini-2" in name:
        return 1_000_000
    if "gemini-1.5-pro" in name:
        return 2_000_000
    if "gemini-1.5" in name:
        return 1_000_000
    return None


def _infer_ollama_context_window(model_name: str) -> int | None:
    mapping = {
        "llama3.1": 128_000,
        "llama3": 8_192,
        "llama2": 4_096,
        "mistral": 8_000,
        "neural-chat": 4_096,
        "openchat": 8_192,
        "starling": 4_096,
    }
    lower = model_name.lower()
    for key, size in mapping.items():
        if key in lower:
            return size
    return 4_096


def _anthropic_maintained_catalog() -> list[ProviderModel]:
    return [
        ProviderModel(
            id=model_id,
            name=label,
            context_window=context_window,
            supports_streaming=True,
            supports_structured_output=True,
            description="Maintained Anthropic model catalog fallback",
        )
        for model_id, label, context_window in ANTHROPIC_MAINTAINED_MODELS
    ]


def _openai_maintained_catalog() -> list[ProviderModel]:
    return [
        ProviderModel(
            id=model_id,
            name=label,
            context_window=context_window,
            supports_streaming=True,
            supports_structured_output=True,
            description="Maintained OpenAI model catalog fallback",
        )
        for model_id, label, context_window in OPENAI_MAINTAINED_MODELS
    ]


def _openrouter_maintained_catalog() -> list[ProviderModel]:
    return [
        ProviderModel(
            id=model_id,
            name=label,
            context_window=context_window,
            supports_streaming=True,
            supports_structured_output=True,
            description="Maintained OpenRouter model catalog fallback",
        )
        for model_id, label, context_window in OPENROUTER_MAINTAINED_MODELS
    ]
