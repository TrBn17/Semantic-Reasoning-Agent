from __future__ import annotations

from typing import Protocol

from semantic_reasoning_agent.db.models import DocumentChunkORM
from semantic_reasoning_agent.domain.ontology.models import ExtractionResult


class OntologyExtractorPort(Protocol):
    def classify_document_domain(self, chunks: list[DocumentChunkORM]) -> str:
        ...

    def extract_ontology_candidates(
        self,
        chunks: list[DocumentChunkORM],
        workspace_id: str | None = None,
    ) -> ExtractionResult:
        ...
