from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal, Mapping

Role = Literal["system", "user", "assistant", "tool"]

FinishReason = Literal[
    "end_turn",
    "tool_use",
    "max_tokens",
    "stop",
    "error",
]

ToolChoice = Literal["auto", "none", "required"] | str


@dataclass(frozen=True)
class LLMToolCall:
    """Single tool invocation request returned by the model.

    ``call_id`` is the provider's tool_use_id (Anthropic) or tool_call.id
    (OpenAI). ``arguments`` is already JSON-decoded into a mapping.
    """

    call_id: str
    tool_name: str
    arguments: Mapping[str, Any]


@dataclass(frozen=True)
class LLMMessage:
    """Unified message shape accepted by every ``ProviderAdapter.run()``.

    - ``role="system"``  — set via ``run(system=...)`` instead of a list entry
      for Anthropic; adapters translate as needed.
    - ``role="user"``    — ``content`` holds the user prompt.
    - ``role="assistant"`` — may carry ``content`` and/or ``tool_calls``.
    - ``role="tool"``    — ``content`` holds the JSON-encoded tool result and
      ``tool_call_id`` echoes the originating LLMToolCall.call_id.
    """

    role: Role
    content: str | None = None
    tool_calls: tuple[LLMToolCall, ...] = ()
    tool_call_id: str | None = None


@dataclass(frozen=True)
class LLMUsage:
    input_tokens: int = 0
    output_tokens: int = 0


@dataclass(frozen=True)
class LLMResponse:
    """Unified response from any provider adapter."""

    content: str | None
    tool_calls: tuple[LLMToolCall, ...] = ()
    finish_reason: FinishReason = "end_turn"
    usage: LLMUsage = field(default_factory=LLMUsage)
    provider: str | None = None
    provider_version: str | None = None
    model: str | None = None
