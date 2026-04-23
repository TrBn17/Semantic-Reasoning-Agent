"""Lightweight BM25 scorer over document chunks.

Production deployments can later swap this with Postgres FTS or Qdrant
hybrid. This pure-Python implementation is sufficient for workspace-
level ranking and keeps the code simple and dependency-free — it reads
directly from already-loaded `DocumentChunkORM` rows.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass

_TOKEN_RE = re.compile(r"[A-Za-z0-9_]+", re.UNICODE)


def tokenize(text: str) -> list[str]:
    return [token.lower() for token in _TOKEN_RE.findall(text or "")]


@dataclass(frozen=True)
class BM25Hit:
    chunk_id: str
    score: float


class BM25Scorer:
    """In-memory BM25 over a fixed corpus.

    Parameters follow the Okapi BM25 defaults: k1=1.5, b=0.75.
    """

    def __init__(self, corpus: list[tuple[str, str]], *, k1: float = 1.5, b: float = 0.75) -> None:
        self._k1 = k1
        self._b = b
        self._chunk_ids: list[str] = []
        self._tokens: list[list[str]] = []
        total_len = 0
        document_frequency: dict[str, int] = {}

        for chunk_id, text in corpus:
            tokens = tokenize(text)
            self._chunk_ids.append(chunk_id)
            self._tokens.append(tokens)
            total_len += len(tokens)
            seen: set[str] = set()
            for token in tokens:
                if token in seen:
                    continue
                seen.add(token)
                document_frequency[token] = document_frequency.get(token, 0) + 1

        self._doc_count = len(corpus)
        self._avg_len = (total_len / self._doc_count) if self._doc_count else 0.0
        self._document_frequency = document_frequency

    def score(self, query: str, *, top_k: int = 10) -> list[BM25Hit]:
        if self._doc_count == 0 or not query.strip():
            return []
        query_tokens = tokenize(query)
        if not query_tokens:
            return []

        idf_cache: dict[str, float] = {}
        for token in set(query_tokens):
            df = self._document_frequency.get(token, 0)
            if df == 0:
                continue
            idf_cache[token] = math.log(1 + (self._doc_count - df + 0.5) / (df + 0.5))

        if not idf_cache:
            return []

        hits: list[BM25Hit] = []
        for index, tokens in enumerate(self._tokens):
            if not tokens:
                continue
            term_frequency: dict[str, int] = {}
            for token in tokens:
                if token in idf_cache:
                    term_frequency[token] = term_frequency.get(token, 0) + 1
            if not term_frequency:
                continue
            doc_len = len(tokens)
            score = 0.0
            for token, frequency in term_frequency.items():
                idf = idf_cache[token]
                denom = frequency + self._k1 * (
                    1 - self._b + self._b * (doc_len / (self._avg_len or 1.0))
                )
                score += idf * ((frequency * (self._k1 + 1)) / denom)
            if score > 0:
                hits.append(BM25Hit(chunk_id=self._chunk_ids[index], score=score))
        hits.sort(key=lambda hit: hit.score, reverse=True)
        return hits[:top_k]
