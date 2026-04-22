from __future__ import annotations

import json
from typing import Any, Sequence

from semantic_reasoning_agent.domain.contracts.llm import (
    FinishReason,
    LLMMessage,
    LLMResponse,
    LLMToolCall,
    LLMUsage,
    ToolChoice,
)
from semantic_reasoning_agent.domain.contracts.tool_spec import ToolSpec
from semantic_reasoning_agent.ports.llm_adapter import ProviderAdapter


_ANTHROPIC_STOP_REASON_MAP: dict[str, FinishReason] = {
    "end_turn": "end_turn",
    "tool_use": "tool_use",
    "max_tokens": "max_tokens",
    "stop_sequence": "stop",
}


class AnthropicAdapter(ProviderAdapter):
    """Anthropic Messages API adapter with native tool use.

    Wraps ``anthropic.Anthropic().messages.create``. Translates between
    ``LLMMessage`` / ``LLMToolCall`` and Anthropic's content-block shapes.
    """

    def __init__(
        self,
        *,
        provider: str = "anthropic",
        api_key: str,
        base_url: str | None = None,
        client: Any | None = None,
    ) -> None:
        self.provider = provider
        self._api_key = api_key
        self._base_url = base_url
        self._client = client

    def _get_client(self) -> Any:
        if self._client is not None:
            return self._client
        from anthropic import Anthropic

        kwargs: dict[str, str] = {"api_key": self._api_key}
        if self._base_url:
            kwargs["base_url"] = self._base_url
        self._client = Anthropic(**kwargs)
        return self._client

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
        workspace_id: str | None = None,
        model_config_service: Any | None = None,
    ) -> LLMResponse:
        api_key = self._api_key
        base_url = self._base_url

        if workspace_id and model_config_service:
            creds = model_config_service.get_provider_credentials(workspace_id)
            p_creds = creds.get(self.provider)
            if p_creds:
                api_key = p_creds.get("api_key") or api_key
                base_url = p_creds.get("base_url") or base_url

        wire_messages, wire_system = _to_anthropic_messages(messages, system=system)
        wire_tools = [spec.to_anthropic_tool() for spec in tools]

        kwargs: dict[str, Any] = {
            "model": model,
            "messages": wire_messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        if wire_system:
            kwargs["system"] = wire_system
        if wire_tools:
            kwargs["tools"] = wire_tools
            kwargs["tool_choice"] = _to_anthropic_tool_choice(tool_choice)

        if api_key == self._api_key and base_url == self._base_url:
            client = self._get_client()
        else:
            import anthropic

            client = anthropic.Anthropic(api_key=api_key, base_url=base_url)
        response = client.messages.create(**kwargs)
        return _parse_anthropic_response(response, model=model, provider=self.provider)


def _to_anthropic_tool_choice(choice: ToolChoice) -> dict[str, Any]:
    if choice == "auto":
        return {"type": "auto"}
    if choice == "none":
        # Anthropic has no explicit "none"; callers should omit tools instead.
        # Preserve intent by still sending auto — adapter omits tools anyway.
        return {"type": "auto"}
    if choice == "required":
        return {"type": "any"}
    return {"type": "tool", "name": choice}


def _to_anthropic_messages(
    messages: Sequence[LLMMessage],
    *,
    system: str | None,
) -> tuple[list[dict[str, Any]], str | None]:
    wire: list[dict[str, Any]] = []
    resolved_system = system
    for message in messages:
        if message.role == "system":
            # System prompts flow via the top-level ``system`` argument.
            if resolved_system is None and message.content:
                resolved_system = message.content
            continue
        if message.role == "assistant":
            content_blocks: list[dict[str, Any]] = []
            if message.content:
                content_blocks.append({"type": "text", "text": message.content})
            for call in message.tool_calls:
                content_blocks.append(
                    {
                        "type": "tool_use",
                        "id": call.call_id,
                        "name": call.tool_name,
                        "input": dict(call.arguments),
                    }
                )
            wire.append({"role": "assistant", "content": content_blocks})
            continue
        if message.role == "tool":
            wire.append(
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "tool_result",
                            "tool_use_id": message.tool_call_id or "",
                            "content": message.content or "",
                        }
                    ],
                }
            )
            continue
        # user
        wire.append({"role": "user", "content": message.content or ""})
    return wire, resolved_system


def _parse_anthropic_response(
    response: Any,
    *,
    model: str,
    provider: str,
) -> LLMResponse:
    texts: list[str] = []
    tool_calls: list[LLMToolCall] = []
    for block in getattr(response, "content", []) or []:
        block_type = getattr(block, "type", "")
        if block_type == "text":
            texts.append(getattr(block, "text", "") or "")
        elif block_type == "tool_use":
            arguments = getattr(block, "input", {}) or {}
            if isinstance(arguments, str):
                try:
                    arguments = json.loads(arguments)
                except json.JSONDecodeError:
                    arguments = {}
            tool_calls.append(
                LLMToolCall(
                    call_id=getattr(block, "id", "") or "",
                    tool_name=getattr(block, "name", "") or "",
                    arguments=arguments,
                )
            )

    stop_reason = getattr(response, "stop_reason", "") or ""
    finish_reason = _ANTHROPIC_STOP_REASON_MAP.get(stop_reason, "end_turn")
    usage_obj = getattr(response, "usage", None)
    usage = LLMUsage(
        input_tokens=getattr(usage_obj, "input_tokens", 0) or 0,
        output_tokens=getattr(usage_obj, "output_tokens", 0) or 0,
    )

    return LLMResponse(
        content=("\n".join(texts).strip() or None) if texts else None,
        tool_calls=tuple(tool_calls),
        finish_reason=finish_reason,
        usage=usage,
        provider=provider,
        provider_version=None,
        model=model,
    )
