from __future__ import annotations

from pathlib import Path

from semantic_reasoning_agent.core.config import Settings
from semantic_reasoning_agent.documents.errors import UnsupportedDocumentTypeError
from semantic_reasoning_agent.documents.models import DocumentIngestionOptions, ParsedDocument
from semantic_reasoning_agent.documents.parsers.base import DocumentParser
from semantic_reasoning_agent.documents.parsers.csv_parser import CsvParser
from semantic_reasoning_agent.documents.parsers.docx_parser import DocxParser
from semantic_reasoning_agent.documents.parsers.pdf_marker_parser import PdfMarkerParser
from semantic_reasoning_agent.documents.parsers.xlsx_parser import XlsxParser


class DocumentParserRegistry:
    def __init__(self, parsers: list[DocumentParser]) -> None:
        self._parsers = parsers
        self._parser_map = {
            document_type: parser
            for parser in parsers
            for document_type in parser.supported_types
        }

    def parse(
        self,
        filename: str,
        content: bytes,
        title: str | None = None,
        *,
        options: DocumentIngestionOptions | None = None,
    ) -> ParsedDocument:
        document_type = Path(filename).suffix.lower().lstrip(".")
        parser = self._parser_map.get(document_type)
        if parser is None:
            raise UnsupportedDocumentTypeError(
                f"Unsupported document type '{document_type}'. Supported types: pdf, docx, xlsx, csv."
            )
        return parser.parse(filename, content, title, options=options)

    def supports(self, filename: str) -> bool:
        return Path(filename).suffix.lower().lstrip(".") in self._parser_map


def build_document_parser(settings: Settings) -> DocumentParserRegistry:
    del settings
    return DocumentParserRegistry(
        [
            PdfMarkerParser(),
            DocxParser(),
            XlsxParser(),
            CsvParser(),
        ]
    )
