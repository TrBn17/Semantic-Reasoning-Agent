from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping
from uuid import UUID


@dataclass(frozen=True)
class ParsedChunk:
    ordinal: int
    text: str
    page: int | None = None
    section: str | None = None
    sheet_name: str | None = None
    row_range: str | None = None
    char_start: int | None = None
    char_end: int | None = None
    metadata: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class ParsedDocument:
    document_id: UUID
    mime_type: str
    chunks: tuple[ParsedChunk, ...]
    extracted_text_length: int
    parser_name: str
    parser_version: str
    page_count: int | None = None
    sheet_names: tuple[str, ...] = ()
    quality_flags: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    ocr_used: bool = False
