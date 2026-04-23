from __future__ import annotations

import re

from semantic_reasoning_agent.documents.models import ParsedChunk

_PAGE_MARKER_PATTERN = re.compile(r"^\d+$")
_PAGE_DIVIDER_PATTERN = re.compile(r"^-{8,}$")


class MarkdownChunker:
    def __init__(self, *, chunk_size: int = 800, overlap: int = 80) -> None:
        self._chunk_size = max(200, chunk_size)
        self._overlap = max(0, min(overlap, self._chunk_size // 2))

    def split(self, markdown: str) -> list[ParsedChunk]:
        heading_chunks = _markdown_to_chunks(markdown)
        if not heading_chunks:
            return []
        oversized = any(len(chunk.text) > self._chunk_size * 2 for chunk in heading_chunks)
        if not oversized:
            return heading_chunks
        return self._split_large_chunks(heading_chunks)

    def _split_large_chunks(self, chunks: list[ParsedChunk]) -> list[ParsedChunk]:
        flattened: list[ParsedChunk] = []
        for chunk in chunks:
            text = chunk.text.strip()
            if len(text) <= self._chunk_size * 2:
                flattened.append(
                    ParsedChunk(
                        text=text,
                        chunk_index=len(flattened),
                        page_number=chunk.page_number,
                        section_title=chunk.section_title,
                        heading_path=chunk.heading_path,
                        table_index=chunk.table_index,
                        sheet_name=chunk.sheet_name,
                        detected_table_id=chunk.detected_table_id,
                        row_start=chunk.row_start,
                        row_end=chunk.row_end,
                        column_headers=chunk.column_headers,
                        metadata=chunk.metadata,
                    )
                )
                continue

            start = 0
            while start < len(text):
                end = min(start + self._chunk_size, len(text))
                segment = text[start:end]
                if end < len(text):
                    boundary = max(segment.rfind("\n\n"), segment.rfind(". "))
                    if boundary > self._chunk_size // 3:
                        end = start + boundary + 1
                        segment = text[start:end]
                segment = segment.strip()
                if segment:
                    flattened.append(
                        ParsedChunk(
                            text=segment,
                            chunk_index=len(flattened),
                            page_number=chunk.page_number,
                            section_title=chunk.section_title,
                            heading_path=chunk.heading_path,
                            table_index=chunk.table_index,
                            sheet_name=chunk.sheet_name,
                            detected_table_id=chunk.detected_table_id,
                            row_start=chunk.row_start,
                            row_end=chunk.row_end,
                            column_headers=chunk.column_headers,
                            metadata=chunk.metadata,
                        )
                    )
                if end >= len(text):
                    break
                start = max(end - self._overlap, start + 1)
        return flattened


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
    if blocks:
        return blocks
    markdown = markdown.strip()
    if not markdown:
        return []
    return [ParsedChunk(text=markdown, chunk_index=0, page_number=current_page)]
