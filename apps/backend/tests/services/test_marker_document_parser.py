from __future__ import annotations

from io import BytesIO

import pytest
from reportlab.pdfgen import canvas

from semantic_reasoning_agent.core.config import Settings
from semantic_reasoning_agent.documents.errors import DocumentProcessingError
from semantic_reasoning_agent.documents.models import DocumentIngestionOptions
from semantic_reasoning_agent.documents.parsers.marker_document_parser import MarkerDocumentParser


def _build_pdf_bytes(text: str) -> bytes:
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer)
    pdf.drawString(72, 720, text)
    pdf.save()
    return buffer.getvalue()


def test_pdf_fast_mode_falls_back_to_pypdf_when_marker_runtime_is_missing() -> None:
    parser = MarkerDocumentParser(Settings(APP_ENV="development"))

    parsed = parser.parse(
        "fallback.pdf",
        _build_pdf_bytes("Fallback parser should still extract this sentence."),
        options=DocumentIngestionOptions(pdf_mode="fast"),
    )

    assert parsed.parser_name == "pypdf"
    assert parsed.page_count == 1
    assert parsed.warnings == ("marker_runtime_unavailable",)
    assert parsed.chunks
    assert "Fallback parser should still extract this sentence." in parsed.chunks[0].text


def test_pdf_accurate_mode_still_requires_marker_runtime() -> None:
    parser = MarkerDocumentParser(Settings(APP_ENV="development"))

    with pytest.raises(DocumentProcessingError, match="marker-pdf\\[full\\] is required"):
        parser.parse(
            "accurate.pdf",
            _build_pdf_bytes("Accurate mode should fail without Marker."),
            options=DocumentIngestionOptions(pdf_mode="accurate"),
        )
