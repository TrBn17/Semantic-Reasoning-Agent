from __future__ import annotations

import json
import os
import re
from functools import lru_cache
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

from PIL import Image
from docx import Document as DocxDocument
from openpyxl import load_workbook
from pypdf import PdfReader

from semantic_reasoning_agent.core.config import Settings
from semantic_reasoning_agent.documents.errors import DocumentProcessingError
from semantic_reasoning_agent.documents.models import (
    DocumentIngestionOptions,
    ParsedArtifact,
    ParsedChunk,
    ParsedDocument,
    StructuredExtractionResult,
)


PARSER_NAME = "marker"
PARSER_VERSION = "marker-v1.10.2"
_PAGE_MARKER_PATTERN = re.compile(r"^\d+$")
_PAGE_DIVIDER_PATTERN = re.compile(r"^-{8,}$")
_IMAGE_EXTENSIONS = ("png", "jpg", "jpeg", "webp", "gif", "bmp", "tif", "tiff")


class MarkerDocumentParser:
    supported_types = (
        "pdf",
        "docx",
        "xlsx",
        "pptx",
        "html",
        "epub",
        *_IMAGE_EXTENSIONS,
    )

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def parse(
        self,
        filename: str,
        content: bytes,
        title: str | None = None,
        *,
        options: DocumentIngestionOptions | None = None,
    ) -> ParsedDocument:
        resolved_options = options or DocumentIngestionOptions()
        document_type = _document_type(filename)
        if self._settings.app_env == "test" and document_type in _FALLBACK_TYPES:
            return _parse_with_fallback(document_type, filename, content, title, resolved_options)
        try:
            return self._parse_with_marker(filename, content, title=title, options=resolved_options)
        except Exception as exc:
            if document_type not in _FALLBACK_TYPES:
                raise DocumentProcessingError(str(exc)) from exc
            return _parse_with_fallback(document_type, filename, content, title, resolved_options)

    def extract_structured(
        self,
        filename: str,
        content: bytes,
        *,
        schema_json: dict[str, Any],
        use_llm: bool,
        force_ocr: bool,
        strip_existing_ocr: bool,
        existing_markdown: str | None = None,
    ) -> StructuredExtractionResult:
        if self._settings.app_env == "test":
            markdown = existing_markdown or content.decode("utf-8", errors="ignore")
            return StructuredExtractionResult(
                parser_name=PARSER_NAME,
                parser_version=PARSER_VERSION,
                result={
                    "schema": schema_json,
                    "items": [line.strip() for line in markdown.splitlines() if line.strip()][:5],
                },
                markdown=markdown,
            )
        self._configure_runtime()
        try:
            from marker.config.parser import ConfigParser
            from marker.converters.extraction import ExtractionConverter
        except ImportError as exc:
            raise DocumentProcessingError("marker-pdf[full] is required for structured extraction.") from exc

        with TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / filename
            path.write_bytes(content)
            config_dict = {
                "page_schema": schema_json,
                "force_ocr": force_ocr,
                "strip_existing_ocr": strip_existing_ocr,
                "use_llm": use_llm,
            }
            if existing_markdown:
                config_dict["existing_markdown"] = existing_markdown
            config = ConfigParser(config_dict)
            converter = ExtractionConverter(
                config=config.generate_config_dict(),
                artifact_dict=_get_marker_models(),
                processor_list=config.get_processors(),
                renderer=config.get_renderer(),
                llm_service=config.get_llm_service(),
                existing_markdown=existing_markdown,
            )
            rendered = converter(str(path))
            payload = rendered.model_dump()
        return StructuredExtractionResult(
            parser_name=PARSER_NAME,
            parser_version=PARSER_VERSION,
            result=payload,
            markdown=payload.get("markdown") or payload.get("original_markdown"),
        )

    def _parse_with_marker(
        self,
        filename: str,
        content: bytes,
        *,
        title: str | None,
        options: DocumentIngestionOptions,
    ) -> ParsedDocument:
        self._configure_runtime()
        try:
            from marker.config.parser import ConfigParser
            from marker.converters.pdf import PdfConverter
            from marker.output import text_from_rendered
        except ImportError as exc:
            raise DocumentProcessingError("marker-pdf[full] is required for document ingestion.") from exc

        with TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / filename
            path.write_bytes(content)
            config = ConfigParser(self._build_marker_config(options))
            converter = PdfConverter(
                config=config.generate_config_dict(),
                artifact_dict=_get_marker_models(),
                processor_list=config.get_processors(),
                renderer=config.get_renderer(),
                llm_service=config.get_llm_service(),
            )
            rendered = converter(str(path))
            text, metadata, images = text_from_rendered(rendered)
            payload = rendered.model_dump()

        markdown = _pick_markdown(text=text, payload=payload)
        if not markdown.strip():
            raise DocumentProcessingError(f"No extractable text was found in '{filename}'.")
        chunks = tuple(_markdown_to_chunks(markdown))
        artifacts = list(_build_image_artifacts(images))
        artifacts.append(
            ParsedArtifact(
                artifact_type="markdown",
                name="document.md",
                content=markdown.encode("utf-8"),
                content_type="text/markdown",
            )
        )
        artifacts.append(
            ParsedArtifact(
                artifact_type="marker_json",
                name="document.json",
                content=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
                content_type="application/json",
            )
        )
        quality_flags = []
        if options.force_ocr:
            quality_flags.append("ocr_forced")
        if metadata.get("page_stats"):
            for page in metadata["page_stats"]:
                method = page.get("text_extraction_method")
                if method == "surya":
                    quality_flags.append("ocr_used")
                    break
        return ParsedDocument(
            document_type=_document_type(filename),
            title=title or Path(filename).stem,
            chunks=chunks,
            parser_name=PARSER_NAME,
            parser_version=PARSER_VERSION,
            markdown=markdown,
            json_payload=payload,
            metadata=metadata or {},
            artifacts=tuple(artifacts),
            page_count=len(metadata.get("page_stats", []) or []) or None,
            quality_flags=tuple(dict.fromkeys(quality_flags)),
            warnings=(),
            ocr_used="ocr_used" in quality_flags or options.force_ocr,
        )

    def _build_marker_config(self, options: DocumentIngestionOptions) -> dict[str, Any]:
        config: dict[str, Any] = {
            "output_format": options.output_format,
            "paginate_output": True,
            "disable_image_extraction": not options.extract_images,
            "force_ocr": options.force_ocr or options.pdf_mode == "accurate",
            "strip_existing_ocr": options.strip_existing_ocr,
            "use_llm": options.use_llm or (
                options.pdf_mode == "accurate" and self._settings.marker_use_llm_in_accurate
            ),
        }
        if self._settings.marker_torch_device:
            config["TORCH_DEVICE"] = self._settings.marker_torch_device
        if self._settings.google_api_key:
            config["google_api_key"] = self._settings.google_api_key
        if self._settings.openai_api_key:
            config["openai_api_key"] = self._settings.openai_api_key
            if self._settings.openai_base_url:
                config["openai_base_url"] = self._settings.openai_base_url
        if self._settings.anthropic_api_key:
            config["claude_api_key"] = self._settings.anthropic_api_key
        return config

    def _configure_runtime(self) -> None:
        cache_dir = Path(self._settings.marker_model_cache_dir)
        cache_dir.mkdir(parents=True, exist_ok=True)
        os.environ.setdefault("MODEL_CACHE_DIR", str(cache_dir))
        if self._settings.marker_torch_device:
            os.environ.setdefault("TORCH_DEVICE", self._settings.marker_torch_device)
        try:
            from surya.settings import settings as surya_settings

            surya_settings.MODEL_CACHE_DIR = str(cache_dir)
            if self._settings.marker_torch_device:
                surya_settings.TORCH_DEVICE = self._settings.marker_torch_device
        except Exception:
            pass


@lru_cache(maxsize=1)
def _get_marker_models():
    from marker.models import create_model_dict

    return create_model_dict()


def _pick_markdown(*, text: str, payload: dict[str, Any]) -> str:
    markdown = payload.get("markdown")
    if isinstance(markdown, str) and markdown.strip():
        return markdown
    if isinstance(text, str):
        return text
    return ""


def _build_image_artifacts(images: dict[str, Image.Image]) -> list[ParsedArtifact]:
    artifacts: list[ParsedArtifact] = []
    for index, (image_id, image) in enumerate((images or {}).items(), start=1):
        buffer = BytesIO()
        image.save(buffer, format="PNG")
        artifacts.append(
            ParsedArtifact(
                artifact_type="image",
                name=f"image-{index}.png",
                content=buffer.getvalue(),
                content_type="image/png",
                metadata={"marker_image_id": image_id},
            )
        )
    return artifacts


def _markdown_to_chunks(markdown: str) -> list[ParsedChunk]:
    heading_stack: list[str] = []
    blocks: list[ParsedChunk] = []
    buffer: list[str] = []
    current_page: int | None = None
    lines = markdown.splitlines()
    index = 0

    def flush() -> None:
        nonlocal buffer
        text = "\n".join(line for line in buffer if line.strip()).strip()
        buffer = []
        if not text:
            return
        section_title = heading_stack[-1] if heading_stack else None
        blocks.append(
            ParsedChunk(
                text=text,
                chunk_index=len(blocks),
                page_number=current_page,
                section_title=section_title,
                heading_path=" > ".join(heading_stack) if heading_stack else None,
            )
        )

    while index < len(lines):
        line = lines[index].rstrip()
        stripped = line.strip()
        next_line = lines[index + 1].strip() if index + 1 < len(lines) else ""
        if _PAGE_MARKER_PATTERN.match(stripped) and _PAGE_DIVIDER_PATTERN.match(next_line):
            flush()
            current_page = int(stripped) + 1
            index += 2
            continue
        if stripped.startswith("#"):
            flush()
            level = len(stripped) - len(stripped.lstrip("#"))
            title = stripped[level:].strip()
            if title:
                heading_stack = heading_stack[: level - 1]
                heading_stack.append(title)
            index += 1
            continue
        if stripped.startswith("![](") or stripped.startswith("<img"):
            index += 1
            continue
        if not stripped and buffer:
            buffer.append("")
            index += 1
            continue
        if stripped:
            buffer.append(stripped)
        index += 1

    flush()
    return blocks or [
        ParsedChunk(text=markdown.strip(), chunk_index=0, page_number=current_page)
    ]


def _document_type(filename: str) -> str:
    return Path(filename).suffix.lower().lstrip(".")


_FALLBACK_TYPES = frozenset({"pdf", "docx", "xlsx"})
_PDF_PAGE_MARKER_PATTERN = re.compile(r"\n\n(\d+)\n-{8,}\n\n")
_WHITESPACE_PATTERN = re.compile(r"\s+")


def _parse_with_fallback(
    document_type: str,
    filename: str,
    content: bytes,
    title: str | None,
    options: DocumentIngestionOptions,
) -> ParsedDocument:
    if document_type == "pdf":
        return _parse_pdf_fallback(filename, content, title, options)
    if document_type == "docx":
        return _parse_docx_fallback(filename, content, title)
    if document_type == "xlsx":
        return _parse_xlsx_fallback(filename, content, title)
    raise DocumentProcessingError(f"Unsupported fallback parser for '{document_type}'.")


def _parse_pdf_fallback(
    filename: str,
    content: bytes,
    title: str | None,
    options: DocumentIngestionOptions,
) -> ParsedDocument:
    try:
        rendered = _render_pdf_with_marker(content, options)
        pages = _extract_pdf_pages(rendered)
        parser_name = "marker"
        parser_version = "marker-v1"
        ocr_used = options.pdf_mode == "accurate"
        quality_flags = ("ocr_forced",) if options.pdf_mode == "accurate" else ()
    except Exception:
        if options.pdf_mode == "accurate":
            raise
        pages = _extract_pdf_pages_with_pypdf(content)
        parser_name = "pypdf"
        parser_version = "pypdf-fast-fallback-v1"
        ocr_used = False
        quality_flags = ("marker_unavailable",)

    chunks: list[ParsedChunk] = []
    for page_number, page_blocks in pages:
        for block in page_blocks:
            text = _normalize_pdf_block(block)
            if not text:
                continue
            section_title = text.splitlines()[0].strip() if text.splitlines() else None
            chunks.append(
                ParsedChunk(
                    text=text,
                    chunk_index=len(chunks),
                    page_number=page_number,
                    section_title=section_title,
                )
            )

    if not chunks:
        raise DocumentProcessingError(f"No extractable text was found in '{filename}'.")

    return ParsedDocument(
        document_type="pdf",
        title=title or Path(filename).stem,
        chunks=tuple(chunks),
        parser_name=parser_name,
        parser_version=parser_version,
        page_count=len(pages),
        quality_flags=quality_flags,
        ocr_used=ocr_used,
    )


def _render_pdf_with_marker(content: bytes, options: DocumentIngestionOptions):
    try:
        from marker.converters.pdf import PdfConverter
        from marker.models import create_model_dict
        from marker.output import text_from_rendered
    except ImportError as exc:
        raise DocumentProcessingError(
            "marker-pdf is required for PDF ingestion. Install project dependencies first."
        ) from exc

    with TemporaryDirectory() as tmpdir:
        pdf_path = Path(tmpdir) / "document.pdf"
        pdf_path.write_bytes(content)
        config: dict[str, object] = {}
        if options.pdf_mode == "accurate":
            config["force_ocr"] = True
        converter = PdfConverter(
            artifact_dict=create_model_dict(),
            config=config or None,
        )
        rendered = converter(str(pdf_path))
        text, _, _ = text_from_rendered(rendered)
    return rendered, text


def _extract_pdf_pages(rendered_payload) -> list[tuple[int, list[str]]]:
    rendered, text = rendered_payload
    if hasattr(rendered, "children") and rendered.children:
        pages: list[tuple[int, list[str]]] = []
        for page_index, page in enumerate(rendered.children, start=1):
            blocks: list[str] = []
            for child in getattr(page, "children", []) or []:
                candidate = (
                    getattr(child, "markdown", None)
                    or getattr(child, "html", None)
                    or getattr(child, "text", None)
                )
                if candidate:
                    blocks.append(str(candidate))
            if blocks:
                pages.append((page_index, blocks))
        if pages:
            return pages

    split_pages = _split_paginated_pdf_text(text)
    if split_pages:
        return split_pages
    return [(1, [text])]


def _split_paginated_pdf_text(text: str) -> list[tuple[int, list[str]]]:
    matches = list(_PDF_PAGE_MARKER_PATTERN.finditer(text))
    if not matches:
        return []
    pages: list[tuple[int, list[str]]] = []
    for index, match in enumerate(matches):
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        page_text = text[start:end].strip()
        if page_text:
            pages.append((int(match.group(1)) + 1, [page_text]))
    return pages


def _extract_pdf_pages_with_pypdf(content: bytes) -> list[tuple[int, list[str]]]:
    reader = PdfReader(BytesIO(content))
    pages: list[tuple[int, list[str]]] = []
    for page_index, page in enumerate(reader.pages, start=1):
        extracted = _normalize_pdf_block(page.extract_text() or "")
        if extracted:
            pages.append((page_index, [extracted]))
    return pages


def _normalize_pdf_block(value: str) -> str:
    lines = [_WHITESPACE_PATTERN.sub(" ", line).strip() for line in str(value).splitlines()]
    return "\n".join(line for line in lines if line)


def _parse_docx_fallback(
    filename: str,
    content: bytes,
    title: str | None,
) -> ParsedDocument:
    document = DocxDocument(BytesIO(content))
    chunks: list[ParsedChunk] = []
    heading_stack: list[str] = []
    paragraph_buffer: list[str] = []

    def flush_paragraphs() -> None:
        if not paragraph_buffer:
            return
        heading_path = " > ".join(heading_stack) if heading_stack else "Document"
        chunks.append(
            ParsedChunk(
                text="\n".join(paragraph_buffer),
                chunk_index=len(chunks),
                section_title=heading_stack[-1] if heading_stack else "Document",
                heading_path=heading_path,
            )
        )
        paragraph_buffer.clear()

    for paragraph in document.paragraphs:
        text = _normalize_inline_text(paragraph.text)
        if not text:
            continue
        style_name = paragraph.style.name if paragraph.style and paragraph.style.name else ""
        if style_name.startswith("Heading"):
            flush_paragraphs()
            level = _extract_heading_level(style_name)
            heading_stack[:] = heading_stack[: level - 1]
            heading_stack.append(text)
            continue
        paragraph_buffer.append(text)

    flush_paragraphs()

    for table_index, table in enumerate(document.tables, start=1):
        rows: list[str] = []
        for row in table.rows:
            cells = [_normalize_inline_text(cell.text) for cell in row.cells]
            cells = [cell for cell in cells if cell]
            if cells:
                rows.append(" | ".join(cells))
        if not rows:
            continue
        heading_path = " > ".join(heading_stack) if heading_stack else "Document"
        chunks.append(
            ParsedChunk(
                text="\n".join(rows),
                chunk_index=len(chunks),
                section_title=heading_stack[-1] if heading_stack else "Document",
                heading_path=heading_path,
                table_index=table_index,
            )
        )

    if not chunks:
        raise DocumentProcessingError(f"No extractable content was found in '{filename}'.")

    return ParsedDocument(
        document_type="docx",
        title=title or Path(filename).stem,
        chunks=tuple(chunks),
        parser_name="python-docx",
        parser_version="docx-structured-v2",
    )


def _normalize_inline_text(value: str) -> str:
    return _WHITESPACE_PATTERN.sub(" ", value or "").strip()


def _extract_heading_level(style_name: str) -> int:
    match = re.search(r"(\d+)$", style_name)
    if match:
        return max(1, int(match.group(1)))
    return 1


def _parse_xlsx_fallback(
    filename: str,
    content: bytes,
    title: str | None,
) -> ParsedDocument:
    workbook = load_workbook(BytesIO(content), data_only=True)
    chunks: list[ParsedChunk] = []
    sheet_names: list[str] = []

    for sheet in workbook.worksheets:
        sheet_names.append(sheet.title)
        non_empty_rows: list[tuple[int, list[str]]] = []
        for row_number, row in enumerate(sheet.iter_rows(values_only=True), start=1):
            values = [_stringify_cell(cell) for cell in row]
            if any(values):
                non_empty_rows.append((row_number, values))

        if not non_empty_rows:
            continue

        header_row_number, header_values = non_empty_rows[0]
        headers = [
            header if header else f"column_{column_index}"
            for column_index, header in enumerate(header_values, start=1)
        ]
        chunks.append(
            ParsedChunk(
                text=f"Sheet: {sheet.title}\nColumns: {', '.join(headers)}",
                chunk_index=len(chunks),
                section_title=sheet.title,
                sheet_name=sheet.title,
                row_start=header_row_number,
                row_end=header_row_number,
                column_headers=tuple(headers),
                detected_table_id=f"{sheet.title}:schema",
            )
        )

        data_rows = non_empty_rows[1:]
        for offset in range(0, len(data_rows), 5):
            group = data_rows[offset : offset + 5]
            lines: list[str] = []
            for row_number, values in group:
                pairs = [
                    f"{header}: {value}"
                    for header, value in zip(headers, values)
                    if value
                ]
                if pairs:
                    lines.append(f"Row {row_number}: " + "; ".join(pairs))
            if not lines:
                continue
            row_start = group[0][0]
            row_end = group[-1][0]
            chunks.append(
                ParsedChunk(
                    text=f"Sheet: {sheet.title}\nColumns: {', '.join(headers)}\n" + "\n".join(lines),
                    chunk_index=len(chunks),
                    section_title=sheet.title,
                    sheet_name=sheet.title,
                    row_start=row_start,
                    row_end=row_end,
                    column_headers=tuple(headers),
                    detected_table_id=f"{sheet.title}:{row_start}-{row_end}",
                )
            )

    if not chunks:
        raise DocumentProcessingError(f"No extractable worksheet content was found in '{filename}'.")

    return ParsedDocument(
        document_type="xlsx",
        title=title or Path(filename).stem,
        chunks=tuple(chunks),
        parser_name="openpyxl",
        parser_version="xlsx-structured-v2",
        sheet_names=tuple(sheet_names),
    )


def _stringify_cell(value: object) -> str:
    if value is None:
        return ""
    return str(value).strip()
