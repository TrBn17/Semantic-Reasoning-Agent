from __future__ import annotations

import json
from collections.abc import Iterable
from typing import Any

from pydantic import BaseModel, Field, ValidationError

from semantic_reasoning_agent.core.config import Settings
from semantic_reasoning_agent.persistence.models import DocumentChunkORM
from semantic_reasoning_agent.domain.ontology.models import (
    ExtractedEntity,
    ExtractedRelation,
    ExtractionResult,
)
from semantic_reasoning_agent.infrastructure.ontology.llm_prompts import build_extraction_prompt
from semantic_reasoning_agent.infrastructure.ontology.rule_extractor import RuleSeedExtractor
from semantic_reasoning_agent.services.model_config_service import ModelConfigService


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
    entities: list[_LLMEntity] = Field(default_factory=list)
    relations: list[_LLMRelation] = Field(default_factory=list)


class LLMStructuredExtractor:
    def __init__(self, settings: Settings, model_config_service: ModelConfigService) -> None:
        self._settings = settings
        self._model_config_service = model_config_service
        self._rule_extractor = RuleSeedExtractor()

    def classify_document_domain(self, chunks: list[DocumentChunkORM]) -> str:
        return self._rule_extractor.classify_document_domain(chunks)

    def extract_ontology_candidates(
        self,
        chunks: list[DocumentChunkORM],
        workspace_id: str | None = None,
    ) -> ExtractionResult:
        provider, model = self._model_config_service.resolve_task_model(
            "ontology_extraction",
            workspace_id,
        )
        if (
            not self._settings.ontology_llm_enabled
            or provider != "anthropic"
            or not self._model_config_service.is_ready(provider, model, workspace_id)
        ):
            return ExtractionResult(domain=self.classify_document_domain(chunks), entities=[], relations=[])
        if not chunks:
            return ExtractionResult(domain="general", entities=[], relations=[])

        text = "\n\n".join(chunk.text for chunk in chunks[: self._settings.ontology_chunk_limit])
        domain = self.classify_document_domain(chunks)
        prompt = build_extraction_prompt(
            domain=domain,
            text=text,
            prompt_version=self._settings.ontology_prompt_version,
        )
        payload = self._invoke_anthropic(prompt, model=model)
        extraction = self._parse_payload(payload)
        return self._to_domain_result(
            extraction,
            domain=domain,
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
        domain: str,
        chunks: Iterable[DocumentChunkORM],
        provider: str,
        model: str,
    ) -> ExtractionResult:
        first_chunk = next(iter(chunks), None)
        source_chunk_id = first_chunk.chunk_id if first_chunk is not None else None
        base_provenance: dict[str, Any] = {
            "extractor": "llm",
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
        return ExtractionResult(domain=domain, entities=entities, relations=relations)
