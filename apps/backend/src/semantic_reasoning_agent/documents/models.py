from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Literal


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


DocumentIngestionMode = Literal["ontology", "retrieval", "both"]


@dataclass(frozen=True)
class DocumentIngestionOptions:
    ingestion_mode: DocumentIngestionMode = "both"

    def to_dict(self) -> dict[str, Any]:
        return {
            "ingestion_mode": self.ingestion_mode,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any] | None) -> "DocumentIngestionOptions":
        if not payload:
            return cls()
        ingestion_mode = str(payload.get("ingestion_mode") or "both").lower()
        if ingestion_mode not in {"ontology", "retrieval", "both"}:
            ingestion_mode = "both"
        return cls(ingestion_mode=ingestion_mode)  # type: ignore[arg-type]


@dataclass(frozen=True)
class ConvertedDocument:
    document_type: str
    title: str
    markdown: str
    converter_name: str
    converter_version: str
    metadata: dict[str, Any] = field(default_factory=dict)
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True)
class ParsedArtifact:
    artifact_type: str
    name: str
    content: bytes
    content_type: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
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
    column_headers: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ParsedDocument:
    document_type: str
    title: str
    chunks: tuple[ParsedChunk, ...]
    parser_name: str
    parser_version: str
    markdown: str | None = None
    html: str | None = None
    json_payload: dict[str, Any] | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    artifacts: tuple[ParsedArtifact, ...] = ()
    page_count: int | None = None
    sheet_names: tuple[str, ...] = ()
    quality_flags: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    ocr_used: bool = False


@dataclass(frozen=True)
class StructuredExtractionResult:
    parser_name: str
    parser_version: str
    result: dict[str, Any]
    markdown: str | None = None
    warnings: tuple[str, ...] = ()


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
    embedding: list[float] | dict[str, int]
    embedding_provider: str | None = None
    embedding_model: str | None = None
    page_number: int | None = None
    section_title: str | None = None
    heading_path: str | None = None
    table_index: int | None = None
    sheet_name: str | None = None
    detected_table_id: str | None = None
    row_start: int | None = None
    row_end: int | None = None
    column_headers: list[str] = field(default_factory=list)
