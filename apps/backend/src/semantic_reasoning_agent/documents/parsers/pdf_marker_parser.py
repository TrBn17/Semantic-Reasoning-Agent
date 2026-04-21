from __future__ import annotations

import re
from io import BytesIO
from pathlib import Path
from tempfile import NamedTemporaryFile

from pypdf import PdfReader

from semantic_reasoning_agent.documents.errors import DocumentProcessingError
from semantic_reasoning_agent.documents.models import DocumentIngestionOptions, ParsedChunk, ParsedDocument


PARSER_NAME = "marker"
PARSER_VERSION = "marker-v1"


class PdfMarkerParser:
    supported_types = ("pdf",)

    def parse(
        self,
        filename: str,
        content: bytes,
        title: str | None = None,
        *,
        options: DocumentIngestionOptions | None = None,
    ) -> ParsedDocument:
        resolved_options = options or DocumentIngestionOptions()
        try:
            rendered = self._render_pdf(content, resolved_options)
            pages = _extract_pages(rendered)
            parser_name = PARSER_NAME
            parser_version = PARSER_VERSION
            ocr_used = resolved_options.pdf_mode == "accurate"
            quality_flags = ("ocr_forced",) if resolved_options.pdf_mode == "accurate" else ()
        except DocumentProcessingError:
            if resolved_options.pdf_mode == "accurate":
                raise
            pages = self._fallback_parse_pdf(content)
            parser_name = "pypdf"
            parser_version = "pypdf-fast-fallback-v1"
            ocr_used = False
            quality_flags = ("marker_unavailable",)
        chunks: list[ParsedChunk] = []

        for page_number, page_blocks in pages:
            for block in page_blocks:
                text = _normalize_block_text(block)
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

        quality_flags = ("ocr_forced",) if resolved_options.pdf_mode == "accurate" else ()
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

    def _render_pdf(self, content: bytes, options: DocumentIngestionOptions):
        try:
            from marker.converters.pdf import PdfConverter
            from marker.models import create_model_dict
            from marker.output import text_from_rendered
        except ImportError as exc:
            raise DocumentProcessingError(
                "marker-pdf is required for PDF ingestion. Install project dependencies first."
            ) from exc

        with NamedTemporaryFile(suffix=".pdf", delete=False) as handle:
            handle.write(content)
            pdf_path = handle.name

        config: dict[str, object] = {}
        if options.pdf_mode == "accurate":
            config["force_ocr"] = True

        converter = PdfConverter(
            artifact_dict=create_model_dict(),
            config=config or None,
        )
        rendered = converter(pdf_path)
        text, _, _ = text_from_rendered(rendered)
        return rendered, text

    def _fallback_parse_pdf(self, content: bytes) -> list[tuple[int, list[str]]]:
        reader = PdfReader(BytesIO(content))
        pages: list[tuple[int, list[str]]] = []
        for page_index, page in enumerate(reader.pages, start=1):
            extracted = _normalize_block_text(page.extract_text() or "")
            if extracted:
                pages.append((page_index, [extracted]))
        return pages


def _extract_pages(rendered_payload) -> list[tuple[int, list[str]]]:
    rendered, text = rendered_payload
    if hasattr(rendered, "children") and rendered.children:
        pages: list[tuple[int, list[str]]] = []
        for page_index, page in enumerate(rendered.children, start=1):
            blocks: list[str] = []
            for child in getattr(page, "children", []) or []:
                candidate = getattr(child, "markdown", None) or getattr(child, "html", None) or getattr(child, "text", None)
                if candidate:
                    blocks.append(str(candidate))
            if blocks:
                pages.append((page_index, blocks))
        if pages:
            return pages

    split_pages = _split_paginated_text(text)
    if split_pages:
        return split_pages
    return [(1, [text])]


def _split_paginated_text(text: str) -> list[tuple[int, list[str]]]:
    pattern = re.compile(r"\n\n(\d+)\n-{8,}\n\n")
    matches = list(pattern.finditer(text))
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


def _normalize_block_text(value: str) -> str:
    lines = [re.sub(r"\s+", " ", line).strip() for line in str(value).splitlines()]
    return "\n".join(line for line in lines if line)
