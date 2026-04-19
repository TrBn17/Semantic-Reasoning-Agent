from __future__ import annotations

import json
from collections.abc import Iterable
from typing import Any

from pydantic import BaseModel, Field, ValidationError

from semantic_reasoning_agent.core.config import Settings
from semantic_reasoning_agent.domain.ontology.models import (
    ExtractedEntity,
    ExtractedRelation,
    ExtractionResult,
)
from semantic_reasoning_agent.infrastructure.ontology.llm_prompts import (
    build_open_domain_prompt,
)
from semantic_reasoning_agent.persistence.models import DocumentChunkORM
from semantic_reasoning_agent.services.model_config_service import ModelConfigService
from semantic_reasoning_agent.tools.ontology.schema_registry import OntologySchemaRegistry


class _LLMEntity(BaseModel):
    name: str
    canonical_name: str
    resolution_key: str
    entity_type: str
    confidence: float
    evidence_text: str
    aliases: list[str] = Field(default_factory=list)


class _LLMRelation(BaseModel):
    source_resolution_key: str
    target_resolution_key: str
    source_name: str
    target_name: str
    relation_type: str
    confidence: float
    evidence_text: str


class _LLMExtraction(BaseModel):
    domain: str = "general"
    entities: list[_LLMEntity] = Field(default_factory=list)
    relations: list[_LLMRelation] = Field(default_factory=list)


class OpenDomainLLMExtractor:
    """LLM-only ontology extractor. No regex patterns, no hardcoded entity
    or relation types, no fixed domain enum.

    The LLM proposes types and the document domain in a single call. Prior
    types observed in the workspace (the emergent schema) are passed as a
    descriptive prior — never as a constraint.
    """

    def __init__(
        self,
        settings: Settings,
        model_config_service: ModelConfigService,
        schema_registry: OntologySchemaRegistry,
    ) -> None:
        self._settings = settings
        self._model_config_service = model_config_service
        self._schema_registry = schema_registry

    def classify_document_domain(self, chunks: list[DocumentChunkORM]) -> str:
        """Domain is emitted by the LLM in the same call as entities/relations.

        Step kept as a pass-through so the orchestrator can continue to
        report the canonical pipeline step. The real domain value is
        attached to the ExtractionResult produced by
        `extract_ontology_candidates`.
        """
        return "pending"

    def extract_ontology_candidates(
        self,
        chunks: list[DocumentChunkORM],
        workspace_id: str | None = None,
    ) -> ExtractionResult:
        if not self._settings.ontology_llm_enabled:
            return ExtractionResult(domain="disabled", entities=[], relations=[])

        if not chunks:
            return ExtractionResult(domain="general", entities=[], relations=[])

        provider, model = self._model_config_service.resolve_task_model(
            "ontology_extraction",
            workspace_id,
        )
        if provider != "anthropic" or not self._model_config_service.is_ready(
            provider, model, workspace_id
        ):
            return ExtractionResult(domain="unavailable", entities=[], relations=[])

        text = "\n\n".join(chunk.text for chunk in chunks[: self._settings.ontology_chunk_limit])
        resolved_workspace_id = workspace_id or self._settings.default_workspace_id
        schema = self._schema_registry.for_workspace(resolved_workspace_id)
        prompt = build_open_domain_prompt(
            text=text,
            known_entity_types=schema.entity_types,
            known_relation_types=schema.relation_types,
            prompt_version=self._settings.ontology_prompt_version,
        )
        payload = self._invoke_anthropic(prompt, model=model)
        extraction = self._parse_payload(payload)
        return self._to_domain_result(
            extraction,
            chunks=chunks,
            provider=provider,
            model=model,
        )

    def _invoke_anthropic(self, prompt: str, *, model: str) -> str:
        from anthropic import Anthropic

        client = Anthropic(api_key=self._settings.anthropic_api_key)
        response = client.messages.create(
            model=model,
            max_tokens=3000,
            temperature=0,
            messages=[{"role": "user", "content": prompt}],
        )
        texts = [
            block.text
            for block in response.content
            if getattr(block, "type", "") == "text" and hasattr(block, "text")
        ]
        return "\n".join(texts).strip()

    @staticmethod
    def _parse_payload(payload: str) -> _LLMExtraction:
        try:
            data = json.loads(payload)
        except json.JSONDecodeError:
            return _LLMExtraction()
        try:
            return _LLMExtraction.model_validate(data)
        except ValidationError:
            return _LLMExtraction()

    def _to_domain_result(
        self,
        extraction: _LLMExtraction,
        *,
        chunks: Iterable[DocumentChunkORM],
        provider: str,
        model: str,
    ) -> ExtractionResult:
        first_chunk = next(iter(chunks), None)
        source_chunk_id = first_chunk.chunk_id if first_chunk is not None else None
        base_provenance: dict[str, Any] = {
            "extractor": "open_domain_llm",
            "provider": provider,
            "model": model,
            "prompt_version": self._settings.ontology_prompt_version,
            "source_chunk_id": source_chunk_id,
        }
        entities = [
            ExtractedEntity(
                name=item.name,
                canonical_name=item.canonical_name,
                resolution_key=item.resolution_key,
                entity_type=item.entity_type,
                confidence=max(0.0, min(1.0, float(item.confidence))),
                source_chunk_id=source_chunk_id,
                evidence_text=item.evidence_text,
                provenance=base_provenance,
                aliases=set(item.aliases),
            )
            for item in extraction.entities
        ]
        relations = [
            ExtractedRelation(
                source_resolution_key=item.source_resolution_key,
                target_resolution_key=item.target_resolution_key,
                source_name=item.source_name,
                target_name=item.target_name,
                relation_type=item.relation_type,
                confidence=max(0.0, min(1.0, float(item.confidence))),
                source_chunk_id=source_chunk_id,
                evidence_text=item.evidence_text,
                provenance=base_provenance,
            )
            for item in extraction.relations
        ]
        return ExtractionResult(
            domain=extraction.domain or "general",
            entities=entities,
            relations=relations,
        )
