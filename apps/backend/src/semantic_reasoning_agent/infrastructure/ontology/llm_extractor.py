from __future__ import annotations

import json
from collections.abc import Iterable
from typing import Any

from pydantic import BaseModel, Field, ValidationError

from semantic_reasoning_agent.core.config import Settings
from semantic_reasoning_agent.domain.contracts.llm import LLMMessage
from semantic_reasoning_agent.domain.ontology.models import (
    ExtractedEntity,
    ExtractedRelation,
    ExtractionResult,
    OntologyNarrative,
    OntologySourceChunk,
)
from semantic_reasoning_agent.infrastructure.llm.registry import AdapterRegistry
from semantic_reasoning_agent.infrastructure.ontology.llm_prompts import (
    build_open_domain_prompt,
)
from semantic_reasoning_agent.ports.task_model_resolver import TaskModelResolverPort
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


class _LLMOntologyNarrative(BaseModel):
    title: str = "Ontology"
    summary: str = ""


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
        model_config_service: TaskModelResolverPort,
        schema_registry: OntologySchemaRegistry,
        adapter_registry: AdapterRegistry,
    ) -> None:
        self._settings = settings
        self._model_config_service = model_config_service
        self._schema_registry = schema_registry
        self._adapter_registry = adapter_registry

    def classify_document_domain(self, chunks: list[OntologySourceChunk]) -> str:
        """Domain is emitted by the LLM in the same call as entities/relations.

        Step kept as a pass-through so the orchestrator can continue to
        report the canonical pipeline step. The real domain value is
        attached to the ExtractionResult produced by
        `extract_ontology_candidates`.
        """
        return "pending"

    def extract_ontology_candidates(
        self,
        chunks: list[OntologySourceChunk],
        workspace_id: str | None = None,
        provider: str | None = None,
        model: str | None = None,
    ) -> ExtractionResult:
        if not self._settings.ontology_llm_enabled:
            return ExtractionResult(domain="disabled", entities=[], relations=[])

        if not chunks:
            return ExtractionResult(domain="general", entities=[], relations=[])

        resolved_provider = provider
        resolved_model = model
        if not resolved_provider or not resolved_model:
            return ExtractionResult(domain="unconfigured", entities=[], relations=[])
        if not self._model_config_service.is_ready(resolved_provider, resolved_model, workspace_id):
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
        payload = self._invoke_model(
            prompt,
            provider=resolved_provider,
            model=resolved_model,
        )
        extraction = self._parse_payload(payload)
        return self._to_domain_result(
            extraction,
            chunks=chunks,
            provider=resolved_provider,
            model=resolved_model,
        )

    def summarize_ontology(
        self,
        chunks: list[OntologySourceChunk],
        *,
        workspace_id: str | None = None,
        provider: str | None = None,
        model: str | None = None,
        domain: str | None = None,
    ) -> OntologyNarrative:
        if not chunks:
            return OntologyNarrative(title="Ontology", summary="")

        resolved_provider = provider
        resolved_model = model
        if (
            not self._settings.ontology_llm_enabled
            or not resolved_provider
            or not resolved_model
            or not self._model_config_service.is_ready(
                resolved_provider,
                resolved_model,
                workspace_id or self._settings.default_workspace_id,
            )
        ):
            return self._fallback_narrative(chunks, domain=domain)

        text = "\n\n".join(chunk.text for chunk in chunks[: self._settings.ontology_chunk_limit])
        prompt = (
            "You generate concise ontology metadata for a backend ontology build.\n"
            "Return strict JSON with keys title and summary.\n"
            "Rules:\n"
            "- title: 3 to 8 words, descriptive, no quotes.\n"
            "- summary: 1 sentence, <= 180 chars.\n"
            "- reflect the document/topic, not generic AI language.\n"
            f"- domain hint: {domain or 'general'}.\n\n"
            f"Source text:\n{text}"
        )
        payload = self._invoke_model(prompt, provider=resolved_provider, model=resolved_model)
        try:
            narrative = _LLMOntologyNarrative.model_validate(json.loads(payload))
        except (json.JSONDecodeError, ValidationError):
            return self._fallback_narrative(chunks, domain=domain)
        title = (narrative.title or "").strip() or "Ontology"
        summary = (narrative.summary or "").strip()
        return OntologyNarrative(title=title[:120], summary=summary[:280])

    def _invoke_model(self, prompt: str, *, provider: str, model: str) -> str:
        adapter = self._adapter_registry.get(provider)
        if adapter is None:
            return ""
        response = adapter.run(
            messages=[LLMMessage(role="user", content=prompt)],
            tools=(),
            tool_choice="none",
            max_tokens=3000,
            temperature=0,
            model=model,
        )
        return (response.content or "").strip()

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
        chunks: Iterable[OntologySourceChunk],
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

    @staticmethod
    def _fallback_narrative(
        chunks: list[OntologySourceChunk],
        *,
        domain: str | None = None,
    ) -> OntologyNarrative:
        text = " ".join(chunk.text for chunk in chunks[:2]).strip()
        words = [word.strip(".,:;!?()[]{}\"'") for word in text.split()]
        words = [word for word in words if word]
        title_tokens = words[:5]
        title = " ".join(title_tokens) if title_tokens else "Ontology"
        if domain and domain not in {"general", "pending"}:
            title = f"{domain.replace('_', ' ').title()} Ontology"
        summary = text[:180]
        return OntologyNarrative(title=title[:120], summary=summary[:280])
