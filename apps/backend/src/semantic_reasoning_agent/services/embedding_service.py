from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any

import httpx

from semantic_reasoning_agent.core.config import Settings
from semantic_reasoning_agent.infrastructure.vector import TokenVectorBackend
from semantic_reasoning_agent.services.model_config_service import ModelConfigService


EmbeddingPayload = list[float] | dict[str, int]


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
        self._token_backend = TokenVectorBackend()

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
        resolved_provider = (provider or defaults.embedding_provider or "token").strip()
        resolved_model = (model or defaults.embedding_model or "token-fallback").strip()

        ready, _ = self._model_config_service.embedding_backend_status(
            resolved_provider,
            resolved_model,
            workspace,
        )
        if resolved_provider.lower() == "cloudflare" and ready:
            try:
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
            except Exception:
                pass

        return EmbeddingRecord(
            values=self._token_backend.embed_text(text),
            provider=resolved_provider,
            model=resolved_model,
            backend="token_fallback",
        )

    def cosine_similarity(self, left: EmbeddingPayload, right: EmbeddingPayload) -> float:
        if isinstance(left, dict) and isinstance(right, dict):
            return self._token_backend.cosine_similarity(left, right)
        if isinstance(left, list) and isinstance(right, list):
            return _dense_cosine_similarity(left, right)
        return 0.0

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
        response = httpx.post(
            f"{str(base_url).rstrip('/')}/embeddings",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={"model": model, "input": text},
            timeout=20.0,
        )
        response.raise_for_status()
        payload = response.json()
        embedding = _extract_embedding(payload)
        if not embedding:
            raise ValueError("Cloudflare embedding response did not include a vector.")
        return embedding


def _extract_embedding(payload: dict[str, Any]) -> list[float]:
    data = payload.get("data")
    if isinstance(data, list) and data:
        first = data[0]
        if isinstance(first, dict) and isinstance(first.get("embedding"), list):
            return [float(item) for item in first["embedding"]]
    result = payload.get("result")
    if isinstance(result, dict):
        nested = result.get("data")
        if isinstance(nested, list) and nested:
            first = nested[0]
            if isinstance(first, dict) and isinstance(first.get("embedding"), list):
                return [float(item) for item in first["embedding"]]
    return []


def _dense_cosine_similarity(left: list[float], right: list[float]) -> float:
    if not left or not right or len(left) != len(right):
        return 0.0
    numerator = sum(l * r for l, r in zip(left, right, strict=False))
    if numerator == 0:
        return 0.0
    left_norm = math.sqrt(sum(value * value for value in left))
    right_norm = math.sqrt(sum(value * value for value in right))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return numerator / (left_norm * right_norm)


__all__ = ["EmbeddingRecord", "EmbeddingService", "EmbeddingPayload"]
