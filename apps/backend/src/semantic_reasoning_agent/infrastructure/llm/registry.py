from dataclasses import dataclass

from semantic_reasoning_agent.ports.llm_adapter import ProviderAdapter
from semantic_reasoning_agent.infrastructure.llm.echo import EchoAdapter


@dataclass(frozen=True)
class AdapterRegistry:
    adapters: dict[str, ProviderAdapter]

    def get(self, provider: str) -> ProviderAdapter | None:
        return self.adapters.get(provider)


def build_adapter_registry() -> AdapterRegistry:
    return AdapterRegistry(adapters={"echo": EchoAdapter()})
