from __future__ import annotations

import json
from typing import Any, Literal, Mapping, Sequence
from urllib import error, request

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


_OLLAMA_FINISH_REASON_MAP: dict[str, FinishReason] = {
    "stop": "end_turn",
    "length": "max_tokens",
}


class OllamaAdapter(ProviderAdapter):
    provider = "ollama"

    def __init__(
        self,
        *,
        base_url: str = "http://localhost:11434",
        timeout_seconds: int = 60,
        opener: Any | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout_seconds = timeout_seconds
        self._opener = opener

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
        del response_format, reasoning_effort
        base_url = self._base_url
        if workspace_id and model_config_service:
            creds = model_config_service.get_provider_credentials(workspace_id)
            provider_creds = creds.get(self.provider) or {}
            base_url = (provider_creds.get("base_url") or base_url).rstrip("/")

        payload = _build_request_payload(
            model=model,
            messages=messages,
            tools=tools,
            tool_choice=tool_choice,
            system=system,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        body = json.dumps(payload).encode("utf-8")
        endpoint = f"{base_url}/api/chat"
        req = request.Request(
            endpoint,
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            if self._opener is not None:
                response = self._opener.open(req, timeout=self._timeout_seconds)
            else:
                response = request.urlopen(req, timeout=self._timeout_seconds)  # noqa: S310
            raw = response.read()
        except error.HTTPError as exc:
            details = exc.read().decode("utf-8", errors="ignore")
            raise RuntimeError(f"Ollama API error ({exc.code}): {details}") from exc
        except error.URLError as exc:
            raise RuntimeError(f"Failed to reach Ollama at {base_url}: {exc}") from exc

        try:
            parsed = json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError as exc:
            raise RuntimeError("Invalid Ollama response payload") from exc

        return _parse_ollama_response(parsed, model=model, provider=self.provider)


def _build_request_payload(
    *,
    model: str,
    messages: Sequence[LLMMessage],
    tools: Sequence[ToolSpec],
    tool_choice: ToolChoice,
    system: str | None,
    max_tokens: int,
    temperature: float,
) -> dict[str, Any]:
    wire_messages = _to_ollama_messages(messages, system=system)
    payload: dict[str, Any] = {
        "model": model,
        "messages": wire_messages,
        "stream": False,
        "options": {
            "temperature": temperature,
            "num_predict": max_tokens,
        },
    }
    if tools:
        payload["tools"] = [spec.to_openai_tool() for spec in tools]
        if tool_choice == "none":
            payload["tools"] = []
        elif tool_choice not in {"auto", "required"}:
            payload["tool_choice"] = {"type": "function", "function": {"name": tool_choice}}
    return payload


def _to_ollama_messages(
    messages: Sequence[LLMMessage],
    *,
    system: str | None,
) -> list[dict[str, Any]]:
    wire: list[dict[str, Any]] = []
    if system:
        wire.append({"role": "system", "content": system})

    for message in messages:
        if message.role == "assistant":
            payload: dict[str, Any] = {"role": "assistant"}
            if message.content:
                payload["content"] = message.content
            if message.tool_calls:
                payload["tool_calls"] = [
                    {
                        "id": call.call_id,
                        "type": "function",
                        "function": {
                            "name": call.tool_name,
                            "arguments": dict(call.arguments),
                        },
                    }
                    for call in message.tool_calls
                ]
            wire.append(payload)
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
        role = "system" if message.role == "system" else "user"
        wire.append({"role": role, "content": message.content or ""})

    return wire


def _parse_ollama_response(
    payload: Mapping[str, Any],
    *,
    model: str,
    provider: str,
) -> LLMResponse:
    message = payload.get("message", {}) or {}
    content = message.get("content") if isinstance(message, Mapping) else None
    raw_tool_calls = message.get("tool_calls", []) if isinstance(message, Mapping) else []
    tool_calls: list[LLMToolCall] = []
    for idx, raw in enumerate(raw_tool_calls):
        if not isinstance(raw, Mapping):
            continue
        function = raw.get("function", {})
        if not isinstance(function, Mapping):
            function = {}
        arguments = function.get("arguments", {})
        if isinstance(arguments, str):
            try:
                arguments = json.loads(arguments)
            except json.JSONDecodeError:
                arguments = {}
        tool_calls.append(
            LLMToolCall(
                call_id=str(raw.get("id") or f"ollama-tool-{idx}"),
                tool_name=str(function.get("name") or ""),
                arguments=dict(arguments) if isinstance(arguments, Mapping) else {},
            )
        )

    done_reason = str(payload.get("done_reason") or "").lower()
    finish_reason = "tool_use" if tool_calls else _OLLAMA_FINISH_REASON_MAP.get(done_reason, "end_turn")

    usage = LLMUsage(
        input_tokens=int(payload.get("prompt_eval_count") or 0),
        output_tokens=int(payload.get("eval_count") or 0),
    )
    return LLMResponse(
        content=str(content) if isinstance(content, str) else None,
        tool_calls=tuple(tool_calls),
        finish_reason=finish_reason,
        usage=usage,
        provider=provider,
        model=model,
    )
