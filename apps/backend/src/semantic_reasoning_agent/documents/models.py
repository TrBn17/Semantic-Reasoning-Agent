from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class DocumentIngestionOptions:
    pdf_mode: str = "fast"
    output_format: str = "markdown"
    use_llm: bool = False
    force_ocr: bool = False
    strip_existing_ocr: bool = False
    extract_images: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "pdf_mode": self.pdf_mode,
            "output_format": self.output_format,
            "use_llm": self.use_llm,
            "force_ocr": self.force_ocr,
            "strip_existing_ocr": self.strip_existing_ocr,
            "extract_images": self.extract_images,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any] | None) -> "DocumentIngestionOptions":
        if not payload:
            return cls()
        pdf_mode = str(payload.get("pdf_mode") or "fast").lower()
        if pdf_mode not in {"fast", "accurate"}:
            pdf_mode = "fast"
        output_format = str(payload.get("output_format") or "markdown").lower()
        if output_format not in {"markdown", "html", "json", "chunks"}:
            output_format = "markdown"
        return cls(
            pdf_mode=pdf_mode,
            output_format=output_format,
            use_llm=bool(payload.get("use_llm", False)),
            force_ocr=bool(payload.get("force_ocr", False)),
            strip_existing_ocr=bool(payload.get("strip_existing_ocr", False)),
            extract_images=bool(payload.get("extract_images", True)),
        )


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
