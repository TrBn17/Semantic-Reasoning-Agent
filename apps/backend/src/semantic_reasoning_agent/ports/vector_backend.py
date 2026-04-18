from __future__ import annotations

from typing import Protocol


class VectorBackendPort(Protocol):
    def embed_text(self, text: str) -> dict[str, int]:
        ...

    def cosine_similarity(self, left: dict[str, int], right: dict[str, int]) -> float:
        ...
