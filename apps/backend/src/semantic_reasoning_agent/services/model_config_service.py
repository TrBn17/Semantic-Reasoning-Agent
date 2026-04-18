from semantic_reasoning_agent.config import Settings, get_settings
from semantic_reasoning_agent.schemas.chat import ModelOption


class ModelConfigService:
    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()

    def _is_provider_key_available(self, provider: str) -> bool:
        if provider == "echo":
            return True
        if provider == "anthropic":
            return bool(self._settings.anthropic_api_key)
        if provider == "openai":
            return bool(self._settings.openai_api_key)
        if provider == "gemini":
            return bool(self._settings.google_api_key)
        if provider == "ollama":
            return bool(self._settings.ollama_base_url)
        return False

    def list_models(self) -> list[ModelOption]:
        return [
            ModelOption(
                provider="echo",
                model="local-echo",
                ready=True,
                reason="Local placeholder adapter for Phase 1 preparation.",
            ),
            ModelOption(
                provider="anthropic",
                model="claude-sonnet-4-5",
                ready=self._is_provider_key_available("anthropic"),
                reason="Requires ANTHROPIC_API_KEY and runtime adapter enablement.",
            ),
            ModelOption(
                provider="openai",
                model="gpt-5-mini",
                ready=self._is_provider_key_available("openai"),
                reason="Requires OPENAI_API_KEY and runtime adapter enablement.",
            ),
            ModelOption(
                provider="gemini",
                model="gemini-2.5-flash",
                ready=self._is_provider_key_available("gemini"),
                reason="Requires GOOGLE_API_KEY and runtime adapter enablement.",
            ),
            ModelOption(
                provider="ollama",
                model="llama3.1",
                ready=self._is_provider_key_available("ollama"),
                reason="Requires OLLAMA_BASE_URL and runtime adapter enablement.",
            ),
        ]

    def is_ready(self, provider: str, model: str) -> bool:
        return any(item.provider == provider and item.model == model and item.ready for item in self.list_models())

    @property
    def default_provider(self) -> str:
        return self._settings.default_provider

    @property
    def default_model(self) -> str:
        return self._settings.default_model
