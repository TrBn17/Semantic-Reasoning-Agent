from __future__ import annotations

from semantic_reasoning_agent.domain.contracts.llm import LLMMessage
from semantic_reasoning_agent.domain.contracts.tool_spec import ToolSpec
from semantic_reasoning_agent.infrastructure.llm.echo import EchoAdapter


def _spec(name: str = "retrieval.internal") -> ToolSpec:
    return ToolSpec(
        tool_name=name,
        tool_family="retrieval",
        tool_type="internal_service",
        version="1.0.0",
        description="Internal RAG.",
        input_schema={"type": "object"},
    )


def test_echo_returns_user_content_with_system_prefix() -> None:
    adapter = EchoAdapter()
    response = adapter.run(
        messages=[LLMMessage(role="user", content="hello world")],
        system="You are helpful.",
        model="local-echo",
    )
    assert response.content == "echo[You are helpful.]: hello world"
    assert response.tool_calls == ()
    assert response.finish_reason == "end_turn"
    assert response.provider == "echo"
    assert response.model == "local-echo"


def test_echo_without_system_uses_plain_prefix() -> None:
    adapter = EchoAdapter()
    response = adapter.run(
        messages=[LLMMessage(role="user", content="ping")],
        model="local-echo",
    )
    assert response.content == "echo: ping"


def test_echo_required_tool_choice_emits_fake_tool_call() -> None:
    adapter = EchoAdapter()
    spec_a = _spec("retrieval.internal")
    spec_b = _spec("ontology.lookup")
    response = adapter.run(
        messages=[LLMMessage(role="user", content="pick one")],
        tools=(spec_a, spec_b),
        tool_choice="required",
        model="local-echo",
    )
    assert response.content is None
    assert len(response.tool_calls) == 1
    assert response.tool_calls[0].tool_name == "retrieval.internal"
    assert response.finish_reason == "tool_use"


def test_echo_auto_with_tools_does_not_invoke_them() -> None:
    adapter = EchoAdapter()
    response = adapter.run(
        messages=[LLMMessage(role="user", content="hi")],
        tools=(_spec(),),
        tool_choice="auto",
        model="local-echo",
    )
    assert response.tool_calls == ()
    assert response.content == "echo: hi"
