"""Per-agent LLM tuning stored under ``policy_config.llm_inference`` (built-in ReAct subgraphs)."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

ReasoningEffort = Literal["none", "low", "medium", "high"]


class LlmInferenceOverrides(BaseModel):
    """Optional overrides; unset fields fall back to the chat provider/model."""

    provider: str | None = None
    model: str | None = None
    temperature: float | None = Field(default=None, ge=0.0, le=2.0)
    max_tokens: int | None = Field(default=None, ge=1, le=262144)
    reasoning_effort: ReasoningEffort | None = None


def llm_inference_from_policy(policy_config: dict | None) -> LlmInferenceOverrides | None:
    raw = (policy_config or {}).get("llm_inference")
    if raw is None or not isinstance(raw, dict):
        return None
    try:
        return LlmInferenceOverrides.model_validate(raw)
    except Exception:
        return None
