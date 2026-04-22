from __future__ import annotations

from pathlib import Path

from semantic_reasoning_agent.core.config import Settings
from semantic_reasoning_agent.documents.errors import UnsupportedDocumentTypeError
from semantic_reasoning_agent.documents.models import DocumentIngestionOptions, ParsedDocument
from semantic_reasoning_agent.documents.parsers.base import DocumentParser
from semantic_reasoning_agent.documents.parsers.csv_parser import CsvParser
from semantic_reasoning_agent.documents.parsers.marker_document_parser import MarkerDocumentParser


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
                f"Unsupported document type '{document_type}'. Supported types: pdf, docx, xlsx, pptx, html, epub, image, csv."
            )
        return parser.parse(filename, content, title, options=options)

    def supports(self, filename: str) -> bool:
        return Path(filename).suffix.lower().lstrip(".") in self._parser_map

    def get_parser(self, filename: str) -> DocumentParser:
        document_type = Path(filename).suffix.lower().lstrip(".")
        parser = self._parser_map.get(document_type)
        if parser is None:
            raise UnsupportedDocumentTypeError(
                f"Unsupported document type '{document_type}'. Supported types: pdf, docx, xlsx, pptx, html, epub, image, csv."
            )
        return parser

    def supported_types(self) -> tuple[str, ...]:
        return tuple(sorted(self._parser_map.keys()))


def build_document_parser(settings: Settings) -> DocumentParserRegistry:
    # Current parser stack still routes through Marker for PDFs while retaining
    # the backend setting for forward compatibility.
    return DocumentParserRegistry(
        [
            MarkerDocumentParser(settings),
            CsvParser(),
        ]
    )
