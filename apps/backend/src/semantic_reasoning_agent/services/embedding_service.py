from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any

import httpx
import openai

from semantic_reasoning_agent.core.config import Settings
from semantic_reasoning_agent.services.model_config_service import ModelConfigService


EmbeddingPayload = list[float]


@dataclass(frozen=True)
class EmbeddingRecord:
    values: EmbeddingPayload
    provider: str
    model: str
    backend: str


class EmbeddingService:
    def __init__(
        self,
        settings: Settings,
        model_config_service: ModelConfigService,
    ) -> None:
        self._settings = settings
        self._model_config_service = model_config_service

    def embed_text(
        self,
        text: str,
        *,
        workspace_id: str | None = None,
        provider: str | None = None,
        model: str | None = None,
    ) -> EmbeddingRecord:
        workspace = workspace_id or self._settings.default_workspace_id
        defaults = self._model_config_service.get_workspace_search_defaults(workspace)
        resolved_provider = (provider or defaults.embedding_provider or "").strip()
        resolved_model = (model or defaults.embedding_model or "").strip()

        ready, reason = self._model_config_service.embedding_backend_status(
            resolved_provider,
            resolved_model,
            workspace,
        )
        if resolved_provider.lower() != "cloudflare":
            raise ValueError(
                f"Embedding provider '{resolved_provider}' is not allowed. Only 'cloudflare' is supported."
            )
        if not ready:
            raise ValueError(reason)
        return EmbeddingRecord(
            values=self._embed_cloudflare(
                text,
                workspace_id=workspace,
                model=resolved_model,
            ),
            provider=resolved_provider,
            model=resolved_model,
            backend="cloudflare",
        )

    def cosine_similarity(self, left: EmbeddingPayload, right: EmbeddingPayload) -> float:
        return _dense_cosine_similarity(left, right)

    def _embed_cloudflare(
        self,
        text: str,
        *,
        workspace_id: str,
        model: str,
    ) -> list[float]:
        credentials = self._model_config_service.get_provider_credentials(workspace_id).get(
            "cloudflare",
            {},
        )
        api_key = credentials.get("api_key")
        base_url = credentials.get("base_url")
        if not api_key or not base_url:
            raise ValueError("Cloudflare embedding credentials are not configured.")
        normalized_model = _normalize_cloudflare_embedding_model(model)
        openai_exc: Exception | None = None
        try:
            # Prefer Cloudflare OpenAI-compatible endpoint first.
            client = openai.OpenAI(api_key=str(api_key), base_url=str(base_url).rstrip("/"))
            response = client.embeddings.create(
                model=normalized_model,
                input=text,
            )
            first = response.data[0] if response.data else None
            if first is not None and isinstance(first.embedding, list):
                return [float(item) for item in first.embedding]
        except Exception as exc:  # noqa: BLE001
            openai_exc = exc

        # Fallback to native Workers AI run endpoint for accounts where
        # OpenAI-compatible embeddings are not enabled/available.
        run_base_url = str(base_url).rstrip("/")
        if run_base_url.endswith("/v1"):
            run_base_url = run_base_url[: -len("/v1")]
        response = httpx.post(
            f"{run_base_url}/run/{normalized_model}",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={"text": text},
            timeout=20.0,
        )
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            detail = ""
            try:
                detail = f" Response: {response.text}"
            except Exception:  # noqa: BLE001
                detail = ""
            if openai_exc is not None:
                raise ValueError(
                    "Cloudflare embeddings failed for both OpenAI-compatible and ai/run APIs. "
                    f"OpenAI-compatible error: {openai_exc}. ai/run error: {exc}.{detail}"
                ) from exc
            raise ValueError(f"Cloudflare ai/run embedding request failed: {exc}.{detail}") from exc
        payload = response.json()
        embedding = _extract_embedding(payload)
        if not embedding:
            raise ValueError("Cloudflare embedding response did not include a vector.")
        return embedding


def _normalize_cloudflare_embedding_model(model: str) -> str:
    normalized = model.strip()
    if not normalized:
        return normalized
    if normalized.startswith("@cf/"):
        return normalized
    # Backward-compatible aliases used in local defaults/UI.
    aliases = {
        "bge-m3": "@cf/baai/bge-m3",
        "bge-base-en-v1.5": "@cf/baai/bge-base-en-v1.5",
        "bge-large-en-v1.5": "@cf/baai/bge-large-en-v1.5",
    }
    return aliases.get(normalized, normalized)

def _extract_embedding(payload: dict[str, Any]) -> list[float]:
    data = payload.get("data")
    if isinstance(data, list) and data:
        first = data[0]
        if isinstance(first, dict) and isinstance(first.get("embedding"), list):
            return [float(item) for item in first["embedding"]]
        if isinstance(first, list):
            return [float(item) for item in first]
    result = payload.get("result")
    if isinstance(result, dict):
        nested = result.get("data")
        if isinstance(nested, list) and nested:
            first = nested[0]
            if isinstance(first, dict) and isinstance(first.get("embedding"), list):
                return [float(item) for item in first["embedding"]]
            if isinstance(first, list):
                return [float(item) for item in first]
    return []


def _dense_cosine_similarity(left: list[float], right: list[float]) -> float:
    if not left or not right or len(left) != len(right):
        return 0.0
    numerator = sum(left_value * right_value for left_value, right_value in zip(left, right, strict=False))
    if numerator == 0:
        return 0.0
    left_norm = math.sqrt(sum(value * value for value in left))
    right_norm = math.sqrt(sum(value * value for value in right))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return numerator / (left_norm * right_norm)


__all__ = ["EmbeddingRecord", "EmbeddingService", "EmbeddingPayload"]
