from __future__ import annotations

from collections.abc import Sequence
from typing import Literal
from uuid import uuid4

from semantic_reasoning_agent.domain.contracts.llm import LLMMessage, LLMResponse, LLMToolCall, ToolChoice
from semantic_reasoning_agent.domain.contracts.tool_spec import ToolSpec
from semantic_reasoning_agent.ports.llm_adapter import ProviderAdapter


class EchoAdapter(ProviderAdapter):
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
        response_format: Literal["json_object", "text"] | None = None,
        reasoning_effort: Literal["low", "medium", "high"] | None = None,
        workspace_id: str | None = None,
        model_config_service=None,
    ) -> LLMResponse:
        del max_tokens, temperature, response_format, reasoning_effort, workspace_id, model_config_service
        user_content = next((message.content for message in reversed(messages) if message.role == "user"), "") or ""
        if tools and tool_choice == "required":
            return LLMResponse(
                content=None,
                tool_calls=(
                    LLMToolCall(
                        call_id=str(uuid4()),
                        tool_name=tools[0].tool_name,
                        arguments={},
                    ),
                ),
                finish_reason="tool_use",
                provider=self.provider,
                model=model,
            )
        prefix = "echo"
        if system:
            prefix = f"echo[{system}]"
        return LLMResponse(
            content=f"{prefix}: {user_content}",
            finish_reason="end_turn",
            provider=self.provider,
            model=model,
        )
