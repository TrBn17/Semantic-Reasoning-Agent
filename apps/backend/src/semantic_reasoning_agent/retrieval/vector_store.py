import math
import re

from semantic_reasoning_agent.retrieval.models import IndexedChunk


TOKEN_PATTERN = re.compile(r"[A-Za-z0-9_]+")


class InMemoryVectorStore:
    def __init__(self) -> None:
        self._chunks: dict[str, IndexedChunk] = {}

    def upsert_chunks(self, chunks: list[IndexedChunk]) -> None:
        for chunk in chunks:
            self._chunks[chunk.chunk_id] = chunk

    def remove_document(self, document_id: str) -> None:
        chunk_ids = [chunk_id for chunk_id, chunk in self._chunks.items() if chunk.document_id == document_id]
        for chunk_id in chunk_ids:
            del self._chunks[chunk_id]

    def search(
        self,
        query: str,
        workspace_id: str,
        document_ids: list[str] | None = None,
        top_k: int = 3,
    ) -> list[tuple[IndexedChunk, float]]:
        query_embedding = self.embed_text(query)
        matches: list[tuple[IndexedChunk, float]] = []
        for chunk in self._chunks.values():
            if chunk.workspace_id != workspace_id:
                continue
            if document_ids and chunk.document_id not in document_ids:
                continue
            score = _cosine_similarity(query_embedding, chunk.embedding)
            if score <= 0:
                continue
            matches.append((chunk, score))
        matches.sort(key=lambda item: item[1], reverse=True)
        return matches[:top_k]

    def reset(self) -> None:
        self._chunks.clear()

    @staticmethod
    def embed_text(text: str) -> dict[str, int]:
        embedding: dict[str, int] = {}
        for token in TOKEN_PATTERN.findall(text.lower()):
            embedding[token] = embedding.get(token, 0) + 1
        return embedding


def _cosine_similarity(left: dict[str, int], right: dict[str, int]) -> float:
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
