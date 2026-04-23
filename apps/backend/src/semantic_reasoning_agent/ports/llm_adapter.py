from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Literal, Sequence

from semantic_reasoning_agent.domain.contracts.llm import (
    LLMMessage,
    LLMResponse,
    ToolChoice,
)
from semantic_reasoning_agent.domain.contracts.tool_spec import ToolSpec


class ProviderAdapter(ABC):
    """Unified function-calling interface across providers — AGENTS.md §9.

    Every provider (Anthropic, OpenAI, …) must implement ``run()`` with
    the same shape. The agentic loop composes ``messages`` + ``tools`` and
    dispatches the returned ``LLMResponse.tool_calls`` through the
    ``ToolRuntime``. Tool schemas are serialized via ``ToolSpec.to_anthropic_tool``
    / ``ToolSpec.to_openai_tool`` inside each adapter.
    """

    provider: str

    @abstractmethod
    def run(
        self,
        *,
        messages: Sequence[LLMMessage],
        tools: Sequence[ToolSpec] = (),
        tool_choice: ToolChoice = "auto",
        system: str | None = None,
        model: str,
        max_tokens: int = 1024,
        temperature: float = 0.0,
        response_format: Literal["json_object", "text"] | None = None,
        reasoning_effort: Literal["low", "medium", "high"] | None = None,
        workspace_id: str | None = None,
        model_config_service: Any | None = None,
    ) -> LLMResponse:
        """Return the next assistant turn. May include text and/or tool calls."""


def legacy_generate_reply(
    adapter: ProviderAdapter,
    prompt: str,
    *,
    system_prompt: str | None = None,
    model: str,
) -> str:
    """Compatibility shim for single-shot text-in/text-out call sites.

    Used by ``chat_stream_service`` during the PR-2 transition. Delete once
    the chat entrypoint routes through the task runtime (PR-4).
    """
    response = adapter.run(
        messages=[LLMMessage(role="user", content=prompt)],
        tools=(),
        tool_choice="none",
        system=system_prompt,
        model=model,
    )
    return response.content or ""
