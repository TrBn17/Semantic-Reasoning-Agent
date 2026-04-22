from __future__ import annotations

from types import SimpleNamespace

from semantic_reasoning_agent.infrastructure.llm.registry import build_adapter_registry


class _FakeModelConfigService:
    def get_provider_credentials(self, workspace_id: str | None = None):  # noqa: ANN001
        return {
            "openai": {"api_key": "oa-key", "base_url": "https://openai.example/v1"},
            "openrouter": {"api_key": "or-key", "base_url": "https://openrouter.ai/api/v1"},
            "anthropic": {"api_key": "an-key", "base_url": "https://anthropic.example/v1"},
            "gemini": {"api_key": "gm-key"},
            "ollama": {"base_url": "http://localhost:11434"},
        }


def test_build_registry_uses_workspace_credentials_for_all_supported_providers() -> None:
    settings = SimpleNamespace(
        openai_api_key=None,
        openai_base_url=None,
        openrouter_api_key=None,
        openrouter_base_url=None,
        anthropic_api_key=None,
        anthropic_base_url=None,
        google_api_key=None,
        ollama_base_url=None,
    )

    registry = build_adapter_registry(
        settings=settings,
        model_config_service=_FakeModelConfigService(),
        workspace_id="ws_1",
    )

    assert set(registry.adapters.keys()) == {
        "openai",
        "openrouter",
        "anthropic",
        "gemini",
        "ollama",
    }
    assert registry.get("openrouter") is not None
    assert registry.get("openrouter").provider == "openrouter"
