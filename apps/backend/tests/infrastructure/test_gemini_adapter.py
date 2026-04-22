from __future__ import annotations

from types import SimpleNamespace

from semantic_reasoning_agent.domain.contracts.llm import LLMMessage
from semantic_reasoning_agent.domain.contracts.tool_spec import ToolSpec
from semantic_reasoning_agent.infrastructure.llm.gemini_adapter import GeminiAdapter


class _FakeModelsApi:
    def __init__(self, response: object) -> None:
        self._response = response
        self.calls: list[dict] = []

    def generate_content(self, **kwargs):  # noqa: ANN001
        self.calls.append(kwargs)
        return self._response


class _FakeClient:
    def __init__(self, response: object) -> None:
        self.models = _FakeModelsApi(response)


def _spec() -> ToolSpec:
    return ToolSpec(
        tool_name="retrieval.internal",
        tool_family="retrieval",
        tool_type="internal_service",
        version="1.0.0",
        description="Internal RAG.",
        input_schema={"type": "object", "properties": {"query": {"type": "string"}}},
    )


def test_gemini_adapter_passes_tools_and_parses_text() -> None:
    fake_response = SimpleNamespace(
        candidates=[
            SimpleNamespace(
                finish_reason="STOP",
                content=SimpleNamespace(parts=[SimpleNamespace(text="hello")]),
            )
        ],
        usage_metadata=SimpleNamespace(prompt_token_count=11, candidates_token_count=5),
    )
    fake_client = _FakeClient(fake_response)
    adapter = GeminiAdapter(api_key="stub", client=fake_client)

    response = adapter.run(
        messages=[LLMMessage(role="user", content="hi")],
        tools=(_spec(),),
        model="gemini-2.5-flash",
        tool_choice="auto",
        system="Be concise.",
    )

    assert response.content == "hello"
    assert response.finish_reason == "end_turn"
    assert response.usage.input_tokens == 11
    assert response.usage.output_tokens == 5
    assert response.provider == "gemini"
    call = fake_client.models.calls[0]
    assert call["model"] == "gemini-2.5-flash"
    assert call["contents"] == [{"role": "user", "parts": [{"text": "hi"}]}]
    assert call["config"]["system_instruction"] == "Be concise."
    assert call["config"]["tools"][0]["functionDeclarations"][0]["name"] == "retrieval.internal"


def test_gemini_adapter_parses_function_call_response() -> None:
    fake_response = SimpleNamespace(
        candidates=[
            SimpleNamespace(
                finish_reason="STOP",
                content=SimpleNamespace(
                    parts=[
                        {
                            "functionCall": {
                                "name": "retrieval.internal",
                                "args": {"query": "loan policy"},
                                "id": "call_1",
                            }
                        }
                    ]
                ),
            )
        ],
        usage_metadata=SimpleNamespace(prompt_token_count=2, candidates_token_count=1),
    )
    adapter = GeminiAdapter(api_key="stub", client=_FakeClient(fake_response))

    response = adapter.run(
        messages=[LLMMessage(role="user", content="find docs")],
        tools=(_spec(),),
        tool_choice="required",
        model="gemini-2.5-flash",
    )

    assert response.finish_reason == "tool_use"
    assert len(response.tool_calls) == 1
    call = response.tool_calls[0]
    assert call.call_id == "call_1"
    assert call.tool_name == "retrieval.internal"
    assert call.arguments == {"query": "loan policy"}
