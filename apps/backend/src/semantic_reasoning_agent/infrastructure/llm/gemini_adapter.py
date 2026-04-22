from __future__ import annotations

from typing import Any, Mapping, Sequence

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


_GEMINI_FINISH_REASON_MAP: dict[str, FinishReason] = {
    "STOP": "end_turn",
    "MAX_TOKENS": "max_tokens",
}


class GeminiAdapter(ProviderAdapter):
    provider = "gemini"

    def __init__(
        self,
        *,
        api_key: str,
        client: Any | None = None,
    ) -> None:
        self._api_key = api_key
        self._client = client

    def _get_client(self, api_key: str) -> Any:
        if self._client is not None:
            return self._client
        from google import genai

        self._client = genai.Client(api_key=api_key)
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
        if workspace_id and model_config_service:
            creds = model_config_service.get_provider_credentials(workspace_id)
            provider_creds = creds.get(self.provider) or {}
            api_key = provider_creds.get("api_key") or api_key

        client = self._get_client(api_key)
        request: dict[str, Any] = {
            "model": model,
            "contents": _to_gemini_contents(messages),
            "config": _build_generation_config(
                tools=tools,
                tool_choice=tool_choice,
                system=system,
                temperature=temperature,
                max_tokens=max_tokens,
            ),
        }
        response = client.models.generate_content(**request)
        return _parse_gemini_response(response, model=model, provider=self.provider)


def _build_generation_config(
    *,
    tools: Sequence[ToolSpec],
    tool_choice: ToolChoice,
    system: str | None,
    temperature: float,
    max_tokens: int,
) -> dict[str, Any]:
    config: dict[str, Any] = {
        "temperature": temperature,
        "max_output_tokens": max_tokens,
    }
    if system:
        config["system_instruction"] = system

    if tools:
        config["tools"] = [spec.to_gemini_tool() for spec in tools]
        if tool_choice == "none":
            config["automatic_function_calling"] = {"disable": True}
        elif tool_choice == "required":
            config["tool_config"] = {"function_calling_config": {"mode": "ANY"}}
        elif isinstance(tool_choice, str) and tool_choice not in {"auto", "none", "required"}:
            config["tool_config"] = {
                "function_calling_config": {
                    "mode": "ANY",
                    "allowed_function_names": [tool_choice],
                }
            }
    return config


def _to_gemini_contents(messages: Sequence[LLMMessage]) -> list[dict[str, Any]]:
    contents: list[dict[str, Any]] = []
    for message in messages:
        if message.role == "system":
            continue
        if message.role == "tool":
            contents.append(
                {
                    "role": "user",
                    "parts": [
                        {
                            "functionResponse": {
                                "name": message.tool_call_id or "tool",
                                "response": {"output": message.content or ""},
                            }
                        }
                    ],
                }
            )
            continue
        role = "model" if message.role == "assistant" else "user"
        parts: list[dict[str, Any]] = []
        if message.content:
            parts.append({"text": message.content})
        if message.role == "assistant" and message.tool_calls:
            for call in message.tool_calls:
                parts.append(
                    {
                        "functionCall": {
                            "name": call.tool_name,
                            "args": dict(call.arguments),
                        }
                    }
                )
        if parts:
            contents.append({"role": role, "parts": parts})
    return contents


def _part_value(part: Any, key: str, alt_key: str | None = None) -> Any:
    if isinstance(part, Mapping):
        if key in part:
            return part[key]
        if alt_key is not None:
            return part.get(alt_key)
        return None
    value = getattr(part, key, None)
    if value is None and alt_key is not None:
        value = getattr(part, alt_key, None)
    return value


def _parse_gemini_response(
    response: Any,
    *,
    model: str,
    provider: str,
) -> LLMResponse:
    candidates = getattr(response, "candidates", None) or []
    if not candidates:
        return LLMResponse(content=None, provider=provider, model=model)

    candidate = candidates[0]
    content_obj = getattr(candidate, "content", None)
    parts = getattr(content_obj, "parts", None) or []
    texts: list[str] = []
    tool_calls: list[LLMToolCall] = []
    for idx, part in enumerate(parts):
        text_value = _part_value(part, "text")
        if isinstance(text_value, str) and text_value:
            texts.append(text_value)
        function_call = _part_value(part, "function_call", "functionCall")
        if function_call:
            if isinstance(function_call, Mapping):
                tool_name = str(function_call.get("name") or "")
                args = function_call.get("args") or {}
                call_id = str(function_call.get("id") or f"gemini-tool-{idx}")
            else:
                tool_name = str(getattr(function_call, "name", "") or "")
                args = getattr(function_call, "args", {}) or {}
                call_id = str(getattr(function_call, "id", "") or f"gemini-tool-{idx}")
            tool_calls.append(
                LLMToolCall(
                    call_id=call_id,
                    tool_name=tool_name,
                    arguments=dict(args) if isinstance(args, Mapping) else {},
                )
            )

    finish_reason_raw = str(getattr(candidate, "finish_reason", "") or "").upper()
    finish_reason = "tool_use" if tool_calls else _GEMINI_FINISH_REASON_MAP.get(
        finish_reason_raw, "end_turn"
    )

    usage_obj = getattr(response, "usage_metadata", None)
    usage = LLMUsage(
        input_tokens=int(getattr(usage_obj, "prompt_token_count", 0) or 0),
        output_tokens=int(getattr(usage_obj, "candidates_token_count", 0) or 0),
    )

    return LLMResponse(
        content=("\n".join(texts).strip() or None) if texts else None,
        tool_calls=tuple(tool_calls),
        finish_reason=finish_reason,
        usage=usage,
        provider=provider,
        model=model,
    )
