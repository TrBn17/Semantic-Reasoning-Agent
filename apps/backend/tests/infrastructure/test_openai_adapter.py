from __future__ import annotations

import json
from types import SimpleNamespace

from semantic_reasoning_agent.domain.contracts.llm import LLMMessage, LLMToolCall
from semantic_reasoning_agent.domain.contracts.tool_spec import ToolSpec
from semantic_reasoning_agent.infrastructure.llm.openai_adapter import OpenAIAdapter


class _FakeCompletions:
    def __init__(self, response: object) -> None:
        self._response = response
        self.calls: list[dict] = []

    def create(self, **kwargs):  # noqa: ANN001
        self.calls.append(kwargs)
        return self._response


class _FakeClient:
    def __init__(self, response: object) -> None:
        self.completions = _FakeCompletions(response)
        self.chat = SimpleNamespace(completions=self.completions)


def _spec() -> ToolSpec:
    return ToolSpec(
        tool_name="retrieval.internal",
        tool_family="retrieval",
        tool_type="internal_service",
        version="1.0.0",
        description="Internal RAG.",
        input_schema={"type": "object", "properties": {"query": {"type": "string"}}},
    )


def test_openai_forwards_tool_schema_and_parses_text_reply() -> None:
    fake_response = SimpleNamespace(
        choices=[
            SimpleNamespace(
                message=SimpleNamespace(content="hi there", tool_calls=None),
                finish_reason="stop",
            )
        ],
        usage=SimpleNamespace(prompt_tokens=7, completion_tokens=3),
    )
    client = _FakeClient(fake_response)
    adapter = OpenAIAdapter(api_key="stub", client=client)

    response = adapter.run(
        messages=[LLMMessage(role="user", content="hi")],
        tools=(_spec(),),
        tool_choice="auto",
        system="Be friendly.",
        model="gpt-5-mini",
    )

    assert response.content == "hi there"
    assert response.finish_reason == "end_turn"
    assert response.usage.input_tokens == 7
    assert response.usage.output_tokens == 3
    assert response.provider == "openai"

    call = client.completions.calls[0]
    assert call["model"] == "gpt-5-mini"
    assert call["messages"][0] == {"role": "system", "content": "Be friendly."}
    assert call["messages"][1] == {"role": "user", "content": "hi"}
    assert call["tools"][0]["type"] == "function"
    assert call["tools"][0]["function"]["name"] == "retrieval.internal"
    assert call["tool_choice"] == "auto"


def test_openai_parses_tool_calls_and_json_arguments() -> None:
    tool_call = SimpleNamespace(
        id="call_abc",
        type="function",
        function=SimpleNamespace(
            name="retrieval.internal",
            arguments=json.dumps({"query": "loan policy", "top_k": 5}),
        ),
    )
    fake_response = SimpleNamespace(
        choices=[
            SimpleNamespace(
                message=SimpleNamespace(content=None, tool_calls=[tool_call]),
                finish_reason="tool_calls",
            )
        ],
        usage=SimpleNamespace(prompt_tokens=15, completion_tokens=5),
    )
    client = _FakeClient(fake_response)
    adapter = OpenAIAdapter(api_key="stub", client=client)

    response = adapter.run(
        messages=[LLMMessage(role="user", content="find loan rules")],
        tools=(_spec(),),
        tool_choice="required",
        model="gpt-5-mini",
    )

    assert response.content is None
    assert response.finish_reason == "tool_use"
    assert len(response.tool_calls) == 1
    parsed = response.tool_calls[0]
    assert parsed.call_id == "call_abc"
    assert parsed.tool_name == "retrieval.internal"
    assert parsed.arguments == {"query": "loan policy", "top_k": 5}
    assert client.completions.calls[0]["tool_choice"] == "required"


def test_openai_encodes_tool_role_and_assistant_tool_calls() -> None:
    fake_response = SimpleNamespace(
        choices=[
            SimpleNamespace(
                message=SimpleNamespace(content="ok", tool_calls=None),
                finish_reason="stop",
            )
        ],
        usage=SimpleNamespace(prompt_tokens=1, completion_tokens=1),
    )
    client = _FakeClient(fake_response)
    adapter = OpenAIAdapter(api_key="stub", client=client)

    adapter.run(
        messages=[
            LLMMessage(role="user", content="run retrieval"),
            LLMMessage(
                role="assistant",
                content=None,
                tool_calls=(
                    LLMToolCall(
                        call_id="call_1",
                        tool_name="retrieval.internal",
                        arguments={"query": "x"},
                    ),
                ),
            ),
            LLMMessage(
                role="tool",
                content='{"evidence": []}',
                tool_call_id="call_1",
            ),
        ],
        tools=(_spec(),),
        model="gpt-5-mini",
    )

    call = client.completions.calls[0]
    assistant_msg = call["messages"][1]
    assert assistant_msg["role"] == "assistant"
    assert assistant_msg["tool_calls"][0]["id"] == "call_1"
    assert json.loads(assistant_msg["tool_calls"][0]["function"]["arguments"]) == {"query": "x"}

    tool_msg = call["messages"][2]
    assert tool_msg["role"] == "tool"
    assert tool_msg["tool_call_id"] == "call_1"
    assert tool_msg["content"] == '{"evidence": []}'
