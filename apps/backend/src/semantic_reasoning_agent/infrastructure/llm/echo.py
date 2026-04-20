from __future__ import annotations

import json
from typing import Sequence

from semantic_reasoning_agent.domain.contracts.llm import (
    LLMMessage,
    LLMResponse,
    LLMToolCall,
    LLMUsage,
    ToolChoice,
)
from semantic_reasoning_agent.domain.contracts.tool_spec import ToolSpec
from semantic_reasoning_agent.ports.llm_adapter import ProviderAdapter


class EchoAdapter(ProviderAdapter):
    """Deterministic test adapter.

    - ``tool_choice="none"`` or no tools → echoes the last user message.
    - ``tool_choice="required"|"any"`` with tools → emits a single fake
      ``LLMToolCall`` for the first tool (arguments = ``{}``) so agentic
      loops can exercise tool wiring without a real provider.
    - ``tool_choice="auto"`` mirrors the "none" path (no tool use by default).
    """

    provider = "echo"

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
    ) -> LLMResponse:
        if tool_choice == "required" and tools:
            first = tools[0]
            return LLMResponse(
                content=None,
                tool_calls=(
                    LLMToolCall(
                        call_id="echo-tool-call-1",
                        tool_name=first.tool_name,
                        arguments={},
                    ),
                ),
                finish_reason="tool_use",
                usage=LLMUsage(),
                provider=self.provider,
                model=model,
            )

        last_user = next(
            (m.content for m in reversed(messages) if m.role == "user" and m.content),
            None,
        )
        prefix = f"echo[{system}]: " if system else "echo: "
        body = last_user or json.dumps({"messages": len(messages)})
        return LLMResponse(
            content=f"{prefix}{body}",
            tool_calls=(),
            finish_reason="end_turn",
            usage=LLMUsage(),
            provider=self.provider,
            model=model,
        )
