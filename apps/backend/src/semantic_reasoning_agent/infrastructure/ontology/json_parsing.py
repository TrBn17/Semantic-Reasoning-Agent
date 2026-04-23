from __future__ import annotations

import importlib
import json
import re
from typing import Any

_THINK_BLOCK_RE = re.compile(r"<think>[\s\S]*?</think>", flags=re.IGNORECASE)
_HARMONY_BLOCK_RE = re.compile(r"<\|channel\|>[\s\S]*?<\|end\|>", flags=re.IGNORECASE)
_CHANNEL_MESSAGE_RE = re.compile(r"<\|start\|>[\s\S]*?<\|message\|>", flags=re.IGNORECASE)
_CODE_FENCE_START_RE = re.compile(r"^\s*```(?:json)?\s*", flags=re.IGNORECASE)
_CODE_FENCE_END_RE = re.compile(r"\s*```\s*$", flags=re.IGNORECASE)


def sanitize_llm_json_payload(raw: str) -> str:
    """Normalize model output before JSON parsing."""
    sanitized = raw.strip()
    sanitized = _THINK_BLOCK_RE.sub("", sanitized)
    sanitized = _HARMONY_BLOCK_RE.sub("", sanitized)
    sanitized = _CHANNEL_MESSAGE_RE.sub("", sanitized)
    sanitized = _CODE_FENCE_START_RE.sub("", sanitized)
    sanitized = _CODE_FENCE_END_RE.sub("", sanitized)
    sanitized = sanitized.strip()

    first_brace = sanitized.find("{")
    last_brace = sanitized.rfind("}")
    if first_brace != -1 and last_brace != -1 and first_brace <= last_brace:
        sanitized = sanitized[first_brace : last_brace + 1]
    return sanitized.strip()


def parse_llm_json(raw: str) -> tuple[dict[str, Any] | None, str | None]:
    """Parse model output as JSON object and return parse error details when it fails."""
    sanitized = sanitize_llm_json_payload(raw)
    if not sanitized:
        return None, "empty_payload"

    try:
        parsed = json.loads(sanitized)
    except json.JSONDecodeError as first_exc:
        try:
            parsed = json.loads(sanitized, strict=False)
        except json.JSONDecodeError as second_exc:
            fallback = _parse_with_optional_demjson(sanitized)
            if fallback is None:
                recovered = _recover_partial_payload(sanitized)
                if recovered is None:
                    return None, f"json_decode_error: {second_exc.msg} (pos={second_exc.pos})"
                return recovered, f"json_recovered_partial: {second_exc.msg} (pos={second_exc.pos})"
            parsed = fallback

    if not isinstance(parsed, dict):
        return None, f"json_root_not_object: {type(parsed).__name__}"
    return parsed, None


def _parse_with_optional_demjson(raw: str) -> dict[str, Any] | None:
    """Best-effort parse using demjson3 when available."""
    try:
        module = importlib.import_module("demjson3")
    except ModuleNotFoundError:
        return None

    try:
        parsed = module.decode(raw)
    except Exception:
        return None
    if isinstance(parsed, dict):
        return parsed
    return None


def _recover_partial_payload(raw: str) -> dict[str, Any] | None:
    """Recover entities/relations arrays from partially valid JSON."""
    entities = _extract_array_items(raw, "entities")
    relations = _extract_array_items(raw, "relations")
    if entities is None and relations is None:
        return None

    payload: dict[str, Any] = {}
    if entities is not None:
        payload["entities"] = entities
    if relations is not None:
        payload["relations"] = relations
    if entities is not None:
        payload["domain"] = _extract_domain(raw) or "general"
    return payload


def _extract_array_items(raw: str, key: str) -> list[dict[str, Any]] | None:
    pattern = re.compile(rf'"{re.escape(key)}"\s*:\s*\[', flags=re.IGNORECASE)
    match = pattern.search(raw)
    if match is None:
        return None

    array_start = match.end() - 1
    object_chunks = _collect_array_object_chunks(raw, array_start)
    items: list[dict[str, Any]] = []
    for chunk in object_chunks:
        try:
            parsed = json.loads(chunk, strict=False)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict):
            items.append(parsed)
    return items


def _collect_array_object_chunks(raw: str, array_start: int) -> list[str]:
    chunks: list[str] = []
    in_string = False
    escape = False
    depth = 0
    object_start: int | None = None
    i = array_start + 1
    while i < len(raw):
        ch = raw[i]
        if in_string:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_string = False
            i += 1
            continue
        if ch == '"':
            in_string = True
            i += 1
            continue
        if ch == "{":
            if depth == 0:
                object_start = i
            depth += 1
            i += 1
            continue
        if ch == "}":
            if depth > 0:
                depth -= 1
                if depth == 0 and object_start is not None:
                    chunks.append(raw[object_start : i + 1])
                    object_start = None
            i += 1
            continue
        if ch == "]" and depth == 0:
            break
        i += 1
    return chunks


def _extract_domain(raw: str) -> str | None:
    match = re.search(r'"domain"\s*:\s*"(?P<value>(?:\\.|[^"\\])*)"', raw, flags=re.IGNORECASE)
    if match is None:
        return None
    try:
        return str(json.loads(f'"{match.group("value")}')).strip() or None
    except json.JSONDecodeError:
        value = match.group("value").strip()
        return value or None
