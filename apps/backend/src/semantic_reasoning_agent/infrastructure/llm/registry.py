from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from semantic_reasoning_agent.core.config import Settings, get_settings
from semantic_reasoning_agent.infrastructure.llm.anthropic_adapter import AnthropicAdapter
from semantic_reasoning_agent.infrastructure.llm.gemini_adapter import GeminiAdapter
from semantic_reasoning_agent.infrastructure.llm.ollama_adapter import OllamaAdapter
from semantic_reasoning_agent.infrastructure.llm.openai_adapter import OpenAIAdapter
from semantic_reasoning_agent.ports.llm_adapter import ProviderAdapter

if TYPE_CHECKING:
    from semantic_reasoning_agent.services.model_config_service import ModelConfigService


@dataclass
class AdapterRegistry:
    adapters: dict[str, ProviderAdapter] = field(default_factory=dict)

    def get(self, provider: str) -> ProviderAdapter | None:
        return self.adapters.get(provider)

    def refresh(self, adapters: dict[str, ProviderAdapter]) -> None:
        self.adapters = dict(adapters)


def build_adapter_registry(
    settings: Settings | None = None,
    *,
    model_config_service: ModelConfigService | None = None,
    workspace_id: str | None = None,
) -> AdapterRegistry:
    cfg = settings or get_settings()
    credentials: dict[str, dict[str, str | None]] = {}
    if model_config_service is not None:
        credentials = model_config_service.get_provider_credentials(workspace_id)

    def resolve_credentials(
        provider: str,
        *,
        env_api_key: str | None,
        env_base_url: str | None,
    ) -> tuple[str | None, str | None]:
        provider_creds = credentials.get(provider) or {}
        return (
            provider_creds.get("api_key") or env_api_key,
            provider_creds.get("base_url") or env_base_url,
        )

    adapters: dict[str, ProviderAdapter] = {}
    anthropic_api_key, anthropic_base_url = resolve_credentials(
        "anthropic",
        env_api_key=cfg.anthropic_api_key,
        env_base_url=cfg.anthropic_base_url,
    )
    if anthropic_api_key:
        adapters["anthropic"] = AnthropicAdapter(
            provider="anthropic",
            api_key=anthropic_api_key,
            base_url=anthropic_base_url,
        )

    openai_api_key, openai_base_url = resolve_credentials(
        "openai",
        env_api_key=cfg.openai_api_key,
        env_base_url=cfg.openai_base_url,
    )
    if openai_api_key:
        adapters["openai"] = OpenAIAdapter(
            provider="openai",
            api_key=openai_api_key,
            base_url=openai_base_url,
        )

    openrouter_api_key, openrouter_base_url = resolve_credentials(
        "openrouter",
        env_api_key=cfg.openrouter_api_key,
        env_base_url=cfg.openrouter_base_url,
    )
    if openrouter_api_key:
        adapters["openrouter"] = OpenAIAdapter(
            provider="openrouter",
            api_key=openrouter_api_key,
            base_url=openrouter_base_url,
        )

    cloudflare_api_key, cloudflare_base_url = resolve_credentials(
        "cloudflare",
        env_api_key=cfg.cloudflare_api_key,
        env_base_url=(
            f"https://api.cloudflare.com/client/v4/accounts/{cfg.cloudflare_account_id}/ai/v1"
            if cfg.cloudflare_account_id
            else None
        ),
    )
    if cloudflare_api_key and cloudflare_base_url:
        adapters["cloudflare"] = OpenAIAdapter(
            provider="cloudflare",
            api_key=cloudflare_api_key,
            base_url=cloudflare_base_url,
        )

    gemini_api_key, _gemini_base_url = resolve_credentials(
        "gemini",
        env_api_key=cfg.google_api_key,
        env_base_url=None,
    )
    if gemini_api_key:
        adapters["gemini"] = GeminiAdapter(api_key=gemini_api_key)

    _ollama_key, ollama_base_url = resolve_credentials(
        "ollama",
        env_api_key=None,
        env_base_url=cfg.ollama_base_url,
    )
    if ollama_base_url:
        adapters["ollama"] = OllamaAdapter(base_url=ollama_base_url)

    return AdapterRegistry(adapters=adapters)
