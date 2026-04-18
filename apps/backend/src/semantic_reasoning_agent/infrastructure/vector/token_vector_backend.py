from __future__ import annotations

import math
import re

from semantic_reasoning_agent.ports.vector_backend import VectorBackendPort

TOKEN_PATTERN = re.compile(r"[A-Za-z0-9_]+")


class TokenVectorBackend(VectorBackendPort):
    def embed_text(self, text: str) -> dict[str, int]:
        embedding: dict[str, int] = {}
        for token in TOKEN_PATTERN.findall(text.lower()):
            embedding[token] = embedding.get(token, 0) + 1
        return embedding

    def cosine_similarity(self, left: dict[str, int], right: dict[str, int]) -> float:
        if not left or not right:
            return 0.0
        numerator = sum(value * right.get(token, 0) for token, value in left.items())
        if numerator == 0:
            return 0.0
        left_norm = math.sqrt(sum(value * value for value in left.values()))
        right_norm = math.sqrt(sum(value * value for value in right.values()))
        if left_norm == 0 or right_norm == 0:
            return 0.0
        return numerator / (left_norm * right_norm)
