from __future__ import annotations

from typing import Protocol

from semantic_reasoning_agent.domain.ontology.models import (
    ExtractionResult,
    OntologyNarrative,
    OntologyDocument,
)


class OntologyExtractorPort(Protocol):
    def classify_document_domain(self, document: OntologyDocument) -> str:
        ...

    def extract_ontology_candidates(
        self,
        document: OntologyDocument,
        workspace_id: str | None = None,
        provider: str | None = None,
        model: str | None = None,
    ) -> ExtractionResult:
        ...

    def summarize_ontology(
        self,
        document: OntologyDocument,
        *,
        workspace_id: str | None = None,
        provider: str | None = None,
        model: str | None = None,
        domain: str | None = None,
    ) -> OntologyNarrative:
        ...
