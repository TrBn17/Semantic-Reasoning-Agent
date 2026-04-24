from types import SimpleNamespace

from semantic_reasoning_agent.domain.contracts.llm import LLMResponse
from semantic_reasoning_agent.infrastructure.llm.registry import AdapterRegistry
from semantic_reasoning_agent.schemas.chat import SendMessageRequest
from semantic_reasoning_agent.schemas.orchestration import OrchestrationMode
from semantic_reasoning_agent.schemas.tasks import TaskResolveRequest
from semantic_reasoning_agent.services.llama_react_orchestrator_service import ReActRunResult
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
        settings=SimpleNamespace(
            default_workspace_id="workspace-demo",
            task_runtime_orchestration_mode="legacy_static_plan",
            task_runtime_react_enabled=True,
        ),
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


def test_resolve_api_request_uses_react_mode_when_requested(monkeypatch) -> None:
    fake_model_config = _FakeModelConfigService()
    fake_adapter = _FakeAdapter()
    service = TaskRuntimeService(
        settings=SimpleNamespace(
            default_workspace_id="workspace-demo",
            task_runtime_orchestration_mode="legacy_static_plan",
            task_runtime_react_enabled=True,
        ),
        model_config_service=fake_model_config,
        adapter_registry=AdapterRegistry(adapters={"openrouter": fake_adapter}),
        tool_runtime=_EmptyToolRuntime(),
    )

    monkeypatch.setattr(
        service,
        "_build_execution_scope",
        lambda profile, **kwargs: SimpleNamespace(  # noqa: ANN001
            allowed_tool_names=(),
            knowledge_pack_ids=(),
            derived_document_ids=(),
            evidence_sources=("internal_chunk", "graph_node", "graph_edge"),
            allow_model_only_fallback=True,
            capability_preset="internal_qa",
            capability_configured=False,
            slot_bindings=(),
        ),
    )
    monkeypatch.setattr(service, "_resolve_workspace_and_agent_profile", lambda request: ("workspace-demo", None))
    monkeypatch.setattr(service._react_orchestrator, "run", lambda **kwargs: ReActRunResult(content="REACT_OK"))

    response = service.resolve_api_request(
        TaskResolveRequest(
            content="use react",
            workspace_id="workspace-demo",
            orchestration_mode="react_two_agent",
            provider="openrouter",
            model="minimax/minimax-m2.5:free",
        )
    )

    assert response.orchestration_mode == "react_two_agent"
    assert response.content == "REACT_OK"


def test_resolve_chat_request_propagates_orchestration_mode(monkeypatch) -> None:
    service = TaskRuntimeService(
        settings=SimpleNamespace(
            default_workspace_id="workspace-demo",
            task_runtime_orchestration_mode="legacy_static_plan",
            task_runtime_react_enabled=True,
        ),
        model_config_service=SimpleNamespace(),
        adapter_registry=AdapterRegistry(adapters={}),
        tool_runtime=SimpleNamespace(),
    )
    captured: dict[str, OrchestrationMode | None] = {"mode": None}

    def _fake_resolve_request(request, **kwargs):  # noqa: ANN001
        captured["mode"] = request.orchestration_mode
        return SimpleNamespace(
            orchestration_mode=request.orchestration_mode or "legacy_static_plan",
            workflow_id="task.resolve.chat",
            content="ok",
            citations=[],
            evidence=[],
            next_action_hints=[],
            tool_calls=[],
        )

    monkeypatch.setattr(service, "resolve_request", _fake_resolve_request)
    service.resolve_chat_request(
        SendMessageRequest(
            conversation_id="conv-1",
            content="hello",
            orchestration_mode="react_two_agent",
        ),
        provider="openrouter",
        model="minimax/minimax-m2.5:free",
    )

    assert captured["mode"] == "react_two_agent"
