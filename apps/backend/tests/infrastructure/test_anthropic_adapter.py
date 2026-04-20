from __future__ import annotations

from types import SimpleNamespace

from semantic_reasoning_agent.domain.contracts.llm import LLMMessage, LLMToolCall
from semantic_reasoning_agent.domain.contracts.tool_spec import ToolSpec
from semantic_reasoning_agent.infrastructure.llm.anthropic_adapter import AnthropicAdapter


class _FakeClient:
    def __init__(self, response: object) -> None:
        self._response = response
        self.calls: list[dict] = []
        self.messages = SimpleNamespace(create=self._create)

    def _create(self, **kwargs):  # noqa: ANN001
        self.calls.append(kwargs)
        return self._response


def _spec(name: str = "retrieval.internal") -> ToolSpec:
    return ToolSpec(
        tool_name=name,
        tool_family="retrieval",
        tool_type="internal_service",
        version="1.0.0",
        description="Internal RAG.",
        input_schema={"type": "object", "properties": {"query": {"type": "string"}}},
    )


def test_anthropic_forwards_tool_schema_and_parses_text_reply() -> None:
    fake_response = SimpleNamespace(
        content=[SimpleNamespace(type="text", text="hello there")],
        stop_reason="end_turn",
        usage=SimpleNamespace(input_tokens=5, output_tokens=4),
    )
    client = _FakeClient(fake_response)
    adapter = AnthropicAdapter(api_key="stub", client=client)

    response = adapter.run(
        messages=[LLMMessage(role="user", content="ping")],
        tools=(_spec(),),
        tool_choice="auto",
        system="Be concise.",
        model="claude-sonnet-4-5",
    )

    assert response.content == "hello there"
    assert response.finish_reason == "end_turn"
    assert response.usage.input_tokens == 5
    assert response.usage.output_tokens == 4
    assert response.provider == "anthropic"

    assert len(client.calls) == 1
    call = client.calls[0]
    assert call["model"] == "claude-sonnet-4-5"
    assert call["system"] == "Be concise."
    assert call["messages"] == [{"role": "user", "content": "ping"}]
    assert call["tools"][0]["name"] == "retrieval.internal"
    assert call["tools"][0]["input_schema"]["properties"]["query"]["type"] == "string"
    assert call["tool_choice"] == {"type": "auto"}


def test_anthropic_parses_tool_use_block() -> None:
    fake_response = SimpleNamespace(
        content=[
            SimpleNamespace(
                type="tool_use",
                id="toolu_01abc",
                name="retrieval.internal",
                input={"query": "loan policy"},
            ),
        ],
        stop_reason="tool_use",
        usage=SimpleNamespace(input_tokens=10, output_tokens=2),
    )
    client = _FakeClient(fake_response)
    adapter = AnthropicAdapter(api_key="stub", client=client)

    response = adapter.run(
        messages=[LLMMessage(role="user", content="find loan rules")],
        tools=(_spec(),),
        tool_choice="required",
        model="claude-sonnet-4-5",
    )

    assert response.content is None
    assert response.finish_reason == "tool_use"
    assert len(response.tool_calls) == 1
    call = response.tool_calls[0]
    assert call.call_id == "toolu_01abc"
    assert call.tool_name == "retrieval.internal"
    assert call.arguments == {"query": "loan policy"}
    assert client.calls[0]["tool_choice"] == {"type": "any"}


def test_anthropic_encodes_tool_result_and_assistant_tool_use() -> None:
    fake_response = SimpleNamespace(
        content=[SimpleNamespace(type="text", text="done")],
        stop_reason="end_turn",
        usage=SimpleNamespace(input_tokens=1, output_tokens=1),
    )
    client = _FakeClient(fake_response)
    adapter = AnthropicAdapter(api_key="stub", client=client)

    adapter.run(
        messages=[
            LLMMessage(role="user", content="run retrieval"),
            LLMMessage(
                role="assistant",
                content=None,
                tool_calls=(
                    LLMToolCall(
                        call_id="toolu_1",
                        tool_name="retrieval.internal",
                        arguments={"query": "x"},
                    ),
                ),
            ),
            LLMMessage(
                role="tool",
                content='{"evidence": []}',
                tool_call_id="toolu_1",
            ),
        ],
        tools=(_spec(),),
        model="claude-sonnet-4-5",
    )

    call = client.calls[0]
    # assistant turn encoded as tool_use content block
    assistant_msg = call["messages"][1]
    assert assistant_msg["role"] == "assistant"
    assert assistant_msg["content"][0]["type"] == "tool_use"
    assert assistant_msg["content"][0]["id"] == "toolu_1"
    # tool result encoded as user turn with tool_result block
    tool_msg = call["messages"][2]
    assert tool_msg["role"] == "user"
    assert tool_msg["content"][0]["type"] == "tool_result"
    assert tool_msg["content"][0]["tool_use_id"] == "toolu_1"
