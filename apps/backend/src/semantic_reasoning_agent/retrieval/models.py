from dataclasses import dataclass, field
from datetime import datetime, timezone


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class ParsedChunk:
    text: str
    chunk_index: int
    page_number: int | None = None
    section_title: str | None = None
    heading_path: str | None = None
    table_index: int | None = None
    sheet_name: str | None = None
    detected_table_id: str | None = None
    row_start: int | None = None
    row_end: int | None = None
    column_headers: list[str] = field(default_factory=list)


@dataclass
class ParsedDocument:
    document_type: str
    title: str
    chunks: list[ParsedChunk]
    parser_version: str


@dataclass
class IndexedChunk:
    chunk_id: str
    document_id: str
    workspace_id: str
    document_title: str
    document_type: str
    text: str
    chunk_index: int
    source_url: str
    parser_version: str
    created_at: datetime
    embedding: dict[str, int]
    page_number: int | None = None
    section_title: str | None = None
    heading_path: str | None = None
    table_index: int | None = None
    sheet_name: str | None = None
    detected_table_id: str | None = None
    row_start: int | None = None
    row_end: int | None = None
    column_headers: list[str] = field(default_factory=list)
