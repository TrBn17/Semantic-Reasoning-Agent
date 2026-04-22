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


_OPENAI_FINISH_REASON_MAP: dict[str, FinishReason] = {
    "stop": "end_turn",
    "tool_calls": "tool_use",
    "length": "max_tokens",
    "content_filter": "stop",
}


class OpenAIAdapter(ProviderAdapter):
    """OpenAI Chat Completions adapter with native function calling.

    Wraps ``openai.OpenAI().chat.completions.create``. Translates between
    ``LLMMessage`` / ``LLMToolCall`` and OpenAI's message/tool shapes.
    """

    provider = "openai"

    def __init__(
        self,
        *,
        api_key: str,
        base_url: str | None = None,
        client: Any | None = None,
    ) -> None:
        self._api_key = api_key
        self._base_url = base_url
        self._client = client

    def _get_client(self) -> Any:
        if self._client is not None:
            return self._client
        import openai

        kwargs: dict[str, Any] = {"api_key": self._api_key}
        if self._base_url:
            kwargs["base_url"] = self._base_url
        self._client = openai.OpenAI(**kwargs)
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
            # Nếu có workspace_id, chúng ta lookup credentials mới nhất từ DB
            # Điều này đảm bảo khi người dùng save settings, chat sẽ dùng key mới ngay
            creds = model_config_service.get_provider_credentials(workspace_id)
            p_creds = creds.get(self.provider)
            if p_creds:
                api_key = p_creds.get("api_key") or api_key
                base_url = p_creds.get("base_url") or base_url

        wire_messages = _to_openai_messages(messages, system=system)
        wire_tools = [spec.to_openai_tool() for spec in tools]

        kwargs: dict[str, Any] = {
            "model": model,
            "messages": wire_messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        if wire_tools:
            kwargs["tools"] = wire_tools
            kwargs["tool_choice"] = _to_openai_tool_choice(tool_choice)

        import openai
        client = openai.OpenAI(api_key=api_key, base_url=base_url)
        response = client.chat.completions.create(**kwargs)
        return _parse_openai_response(response, model=model, provider=self.provider)


def _to_openai_tool_choice(choice: ToolChoice) -> Any:
    if choice in ("auto", "none", "required"):
        return choice
    return {"type": "function", "function": {"name": choice}}


def _to_openai_messages(
    messages: Sequence[LLMMessage],
    *,
    system: str | None,
) -> list[dict[str, Any]]:
    wire: list[dict[str, Any]] = []
    if system:
        wire.append({"role": "system", "content": system})
    for message in messages:
        if message.role == "system":
            wire.append({"role": "system", "content": message.content or ""})
            continue
        if message.role == "assistant":
            entry: dict[str, Any] = {"role": "assistant"}
            if message.content:
                entry["content"] = message.content
            if message.tool_calls:
                entry["tool_calls"] = [
                    {
                        "id": call.call_id,
                        "type": "function",
                        "function": {
                            "name": call.tool_name,
                            "arguments": json.dumps(dict(call.arguments)),
                        },
                    }
                    for call in message.tool_calls
                ]
            wire.append(entry)
            continue
        if message.role == "tool":
            wire.append(
                {
                    "role": "tool",
                    "tool_call_id": message.tool_call_id or "",
                    "content": message.content or "",
                }
            )
            continue
        wire.append({"role": "user", "content": message.content or ""})
    return wire


def _parse_openai_response(
    response: Any,
    *,
    model: str,
    provider: str,
) -> LLMResponse:
    choices = getattr(response, "choices", None) or []
    if not choices:
        return LLMResponse(content=None, provider=provider, model=model)
    choice = choices[0]
    message = getattr(choice, "message", None)
    content = getattr(message, "content", None) if message is not None else None

    tool_calls_raw = getattr(message, "tool_calls", None) or [] if message is not None else []
    tool_calls: list[LLMToolCall] = []
    for tc in tool_calls_raw:
        function = getattr(tc, "function", None)
        raw_arguments = getattr(function, "arguments", "") if function is not None else ""
        if isinstance(raw_arguments, str):
            try:
                arguments: dict[str, Any] = json.loads(raw_arguments) if raw_arguments else {}
            except json.JSONDecodeError:
                arguments = {}
        else:
            arguments = dict(raw_arguments or {})
        tool_calls.append(
            LLMToolCall(
                call_id=getattr(tc, "id", "") or "",
                tool_name=getattr(function, "name", "") or "",
                arguments=arguments,
            )
        )

    finish_reason_raw = getattr(choice, "finish_reason", "") or ""
    finish_reason = _OPENAI_FINISH_REASON_MAP.get(finish_reason_raw, "end_turn")

    usage_obj = getattr(response, "usage", None)
    usage = LLMUsage(
        input_tokens=getattr(usage_obj, "prompt_tokens", 0) or 0,
        output_tokens=getattr(usage_obj, "completion_tokens", 0) or 0,
    )

    return LLMResponse(
        content=content,
        tool_calls=tuple(tool_calls),
        finish_reason=finish_reason,
        usage=usage,
        provider=provider,
        model=model,
    )
