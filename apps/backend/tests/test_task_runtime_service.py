from types import SimpleNamespace

from semantic_reasoning_agent.domain.contracts.llm import LLMResponse
from semantic_reasoning_agent.infrastructure.llm.registry import AdapterRegistry
from semantic_reasoning_agent.schemas.tasks import TaskResolveRequest
from semantic_reasoning_agent.services.task_runtime import TaskRuntimeService


class _FakeModelConfigService:
    def __init__(self) -> None:
        self.readiness_checks: list[tuple[str, str, str | None]] = []

    def is_ready(self, provider: str, model: str, workspace_id: str | None = None) -> bool:
        self.readiness_checks.append((provider, model, workspace_id))
        return provider == "openrouter" and model == "minimax/minimax-m2.5:free"


class _FakeAdapter:
    provider = "openrouter"

    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def run(self, **kwargs) -> LLMResponse:  # noqa: ANN003
        self.calls.append(kwargs)
        return LLMResponse(
            content="TASK_RESOLVE_OPENROUTER_OK",
            provider="openrouter",
            model="minimax/minimax-m2.5:free",
        )


class _EmptyToolRuntime:
    def invoke(self, envelope):  # noqa: ANN001
        return SimpleNamespace(evidence=(), next_action_hints=("no_data",))


def test_resolve_api_request_uses_explicit_provider_and_model_for_fallback() -> None:
    fake_model_config = _FakeModelConfigService()
    fake_adapter = _FakeAdapter()
    service = TaskRuntimeService(
        settings=SimpleNamespace(default_workspace_id="workspace-demo"),
        model_config_service=fake_model_config,
        adapter_registry=AdapterRegistry(adapters={"openrouter": fake_adapter}),
        tool_runtime=_EmptyToolRuntime(),
    )

    response = service.resolve_api_request(
        TaskResolveRequest(
            content="Reply with exactly: TASK_RESOLVE_OPENROUTER_OK",
            provider="openrouter",
            model="minimax/minimax-m2.5:free",
            workspace_id="workspace-demo",
            use_retrieval=False,
        )
    )

    assert response.content == "TASK_RESOLVE_OPENROUTER_OK"
    assert response.output_type == "answer"
    assert response.citations == []
    assert fake_model_config.readiness_checks == [
        ("openrouter", "minimax/minimax-m2.5:free", "workspace-demo")
    ]
    assert len(fake_adapter.calls) == 1
    assert fake_adapter.calls[0]["model"] == "minimax/minimax-m2.5:free"
