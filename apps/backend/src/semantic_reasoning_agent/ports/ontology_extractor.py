from __future__ import annotations

from typing import Protocol

from semantic_reasoning_agent.domain.ontology.models import (
    ExtractionResult,
    OntologyNarrative,
    OntologySourceChunk,
)


class OntologyExtractorPort(Protocol):
    def classify_document_domain(self, chunks: list[OntologySourceChunk]) -> str:
        ...

    def extract_ontology_candidates(
        self,
        chunks: list[OntologySourceChunk],
        workspace_id: str | None = None,
        provider: str | None = None,
        model: str | None = None,
    ) -> ExtractionResult:
        ...

    def summarize_ontology(
        self,
        chunks: list[OntologySourceChunk],
        *,
        workspace_id: str | None = None,
        provider: str | None = None,
        model: str | None = None,
        domain: str | None = None,
    ) -> OntologyNarrative:
        ...
