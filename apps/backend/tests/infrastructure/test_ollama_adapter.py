from __future__ import annotations

import json

from semantic_reasoning_agent.domain.contracts.llm import LLMMessage
from semantic_reasoning_agent.domain.contracts.tool_spec import ToolSpec
from semantic_reasoning_agent.infrastructure.llm.ollama_adapter import OllamaAdapter


class _FakeHttpResponse:
    def __init__(self, payload: dict) -> None:
        self._payload = payload

    def read(self) -> bytes:
        return json.dumps(self._payload).encode("utf-8")


class _FakeOpener:
    def __init__(self, payload: dict) -> None:
        self._payload = payload
        self.requests = []

    def open(self, req, timeout=None):  # noqa: ANN001
        self.requests.append((req, timeout))
        return _FakeHttpResponse(self._payload)


def _spec() -> ToolSpec:
    return ToolSpec(
        tool_name="retrieval.internal",
        tool_family="retrieval",
        tool_type="internal_service",
        version="1.0.0",
        description="Internal RAG.",
        input_schema={"type": "object", "properties": {"query": {"type": "string"}}},
    )


def test_ollama_adapter_serializes_request_and_parses_text() -> None:
    opener = _FakeOpener(
        payload={
            "done_reason": "stop",
            "message": {"role": "assistant", "content": "ok"},
            "prompt_eval_count": 9,
            "eval_count": 3,
        }
    )
    adapter = OllamaAdapter(base_url="http://localhost:11434", opener=opener)

    response = adapter.run(
        messages=[LLMMessage(role="user", content="hello")],
        tools=(_spec(),),
        tool_choice="auto",
        model="qwen3:8b",
    )

    assert response.content == "ok"
    assert response.finish_reason == "end_turn"
    assert response.usage.input_tokens == 9
    assert response.usage.output_tokens == 3
    assert response.provider == "ollama"
    req, timeout = opener.requests[0]
    assert timeout == 60
    payload = json.loads(req.data.decode("utf-8"))
    assert payload["model"] == "qwen3:8b"
    assert payload["messages"][0] == {"role": "user", "content": "hello"}
    assert payload["tools"][0]["function"]["name"] == "retrieval.internal"


def test_ollama_adapter_parses_tool_calls() -> None:
    opener = _FakeOpener(
        payload={
            "done_reason": "stop",
            "message": {
                "role": "assistant",
                "tool_calls": [
                    {
                        "id": "call_1",
                        "function": {
                            "name": "retrieval.internal",
                            "arguments": {"query": "policy"},
                        },
                    }
                ],
            },
        }
    )
    adapter = OllamaAdapter(opener=opener)

    response = adapter.run(
        messages=[LLMMessage(role="user", content="find docs")],
        tools=(_spec(),),
        tool_choice="required",
        model="qwen3:8b",
    )

    assert response.finish_reason == "tool_use"
    assert len(response.tool_calls) == 1
    call = response.tool_calls[0]
    assert call.call_id == "call_1"
    assert call.tool_name == "retrieval.internal"
    assert call.arguments == {"query": "policy"}
