from __future__ import annotations

from typing import Protocol

from semantic_reasoning_agent.domain.ontology.models import ExtractionResult, OntologySourceChunk


class OntologyExtractorPort(Protocol):
    def classify_document_domain(self, chunks: list[OntologySourceChunk]) -> str:
        ...

    def extract_ontology_candidates(
        self,
        chunks: list[OntologySourceChunk],
        workspace_id: str | None = None,
    ) -> ExtractionResult:
        ...
