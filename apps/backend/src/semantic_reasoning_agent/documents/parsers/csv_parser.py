from __future__ import annotations

import csv
from io import StringIO
from pathlib import Path

from semantic_reasoning_agent.documents.errors import DocumentProcessingError
from semantic_reasoning_agent.documents.models import DocumentIngestionOptions, ParsedChunk, ParsedDocument


PARSER_NAME = "stdlib-csv"
PARSER_VERSION = "csv-structured-v1"


class CsvParser:
    supported_types = ("csv",)

    def parse(
        self,
        filename: str,
        content: bytes,
        title: str | None = None,
        *,
        options: DocumentIngestionOptions | None = None,
    ) -> ParsedDocument:
        del options
        text = _decode_csv_bytes(content)
        rows = list(_read_rows(text))
        if not rows:
            raise DocumentProcessingError(f"No extractable rows were found in '{filename}'.")

        header_values = rows[0][1]
        headers = [
            header if header else f"column_{column_index}"
            for column_index, header in enumerate(header_values, start=1)
        ]
        chunks: list[ParsedChunk] = [
            ParsedChunk(
                text=f"CSV: {Path(filename).name}\nColumns: {', '.join(headers)}",
                chunk_index=0,
                section_title="CSV",
                row_start=rows[0][0],
                row_end=rows[0][0],
                column_headers=tuple(headers),
                detected_table_id="csv:schema",
            )
        ]

        data_rows = rows[1:]
        for offset in range(0, len(data_rows), 10):
            group = data_rows[offset : offset + 10]
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
                    text=f"CSV: {Path(filename).name}\nColumns: {', '.join(headers)}\n" + "\n".join(lines),
                    chunk_index=len(chunks),
                    section_title="CSV",
                    row_start=row_start,
                    row_end=row_end,
                    column_headers=tuple(headers),
                    detected_table_id=f"csv:{row_start}-{row_end}",
                )
            )

        return ParsedDocument(
            document_type="csv",
            title=title or Path(filename).stem,
            chunks=tuple(chunks),
            parser_name=PARSER_NAME,
            parser_version=PARSER_VERSION,
        )


def _decode_csv_bytes(content: bytes) -> str:
    for encoding in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
        try:
            return content.decode(encoding)
        except UnicodeDecodeError:
            continue
    return content.decode("latin-1", errors="ignore")


def _read_rows(text: str) -> list[tuple[int, list[str]]]:
    sample = text[:4096]
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",;\t|")
    except csv.Error:
        dialect = csv.excel

    reader = csv.reader(StringIO(text), dialect)
    rows: list[tuple[int, list[str]]] = []
    for row_number, row in enumerate(reader, start=1):
        values = [str(cell).strip() for cell in row]
        if any(values):
            rows.append((row_number, values))
    return rows
