from __future__ import annotations

from dataclasses import dataclass

from semantic_reasoning_agent.core.config import Settings, get_settings
from semantic_reasoning_agent.infrastructure.llm.anthropic_adapter import AnthropicAdapter
from semantic_reasoning_agent.infrastructure.llm.echo import EchoAdapter
from semantic_reasoning_agent.infrastructure.llm.openai_adapter import OpenAIAdapter
from semantic_reasoning_agent.ports.llm_adapter import ProviderAdapter


@dataclass(frozen=True)
class AdapterRegistry:
    adapters: dict[str, ProviderAdapter]

    def get(self, provider: str) -> ProviderAdapter | None:
        return self.adapters.get(provider)


def build_adapter_registry(settings: Settings | None = None) -> AdapterRegistry:
    cfg = settings or get_settings()
    adapters: dict[str, ProviderAdapter] = {"echo": EchoAdapter()}
    if cfg.anthropic_api_key:
        adapters["anthropic"] = AnthropicAdapter(
            api_key=cfg.anthropic_api_key,
            base_url=cfg.anthropic_base_url,
        )
    if cfg.openai_api_key:
        adapters["openai"] = OpenAIAdapter(api_key=cfg.openai_api_key)
    return AdapterRegistry(adapters=adapters)
