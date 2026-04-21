from __future__ import annotations

from typing import Protocol

from semantic_reasoning_agent.documents.models import DocumentIngestionOptions, ParsedDocument


class DocumentParser(Protocol):
    supported_types: tuple[str, ...]

    def parse(
        self,
        filename: str,
        content: bytes,
        title: str | None = None,
        *,
        options: DocumentIngestionOptions | None = None,
    ) -> ParsedDocument:
        ...
