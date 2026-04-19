from __future__ import annotations

from typing import Protocol

from semantic_reasoning_agent.infrastructure.parsers.models import ParsedDocument


class ParserPort(Protocol):
    """Port for document parsers.

    Implementations consume raw bytes plus the original filename and return a
    normalized `ParsedDocument` whose chunks are ready for embedding/index.
    """

    def parse(self, filename: str, content: bytes, title: str | None = None) -> ParsedDocument:
        ...
