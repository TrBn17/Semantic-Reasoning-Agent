from __future__ import annotations

from collections import Counter
from typing import Any, Literal

from pydantic import BaseModel, Field, ValidationError

from semantic_reasoning_agent.core.config import Settings
from semantic_reasoning_agent.domain.contracts.llm import LLMMessage, LLMResponse
from semantic_reasoning_agent.domain.ontology.models import (
    ExtractedFact,
    ExtractedEntity,
    ExtractedRelation,
    ExtractionResult,
    OntologyDocument,
    OntologyNarrative,
    QueryRuleSpec,
)
from semantic_reasoning_agent.infrastructure.llm.registry import AdapterRegistry
from semantic_reasoning_agent.infrastructure.ontology.chunking import chunk_for_extraction
from semantic_reasoning_agent.infrastructure.ontology.json_parsing import parse_llm_json, sanitize_llm_json_payload
from semantic_reasoning_agent.infrastructure.ontology.llm_prompts import (
    build_entity_extraction_prompt,
    build_relation_extraction_prompt,
    build_summary_prompt,
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
    query_rules: list[dict[str, Any]] = Field(default_factory=list)
    facts: list[dict[str, Any]] = Field(default_factory=list)


class _LLMRelation(BaseModel):
    source_resolution_key: str
    target_resolution_key: str
    source_name: str
    target_name: str
    relation_type: str
    confidence: float
    evidence_text: str
    query_rules: list[dict[str, Any]] = Field(default_factory=list)
    facts: list[dict[str, Any]] = Field(default_factory=list)


class _LLMEntityExtraction(BaseModel):
    domain: str = "general"
    entities: list[_LLMEntity] = Field(default_factory=list)


class _LLMRelationExtraction(BaseModel):
    relations: list[_LLMRelation] = Field(default_factory=list)


class _LLMOntologyNarrative(BaseModel):
    title: str = "Ontology"
    summary: str = ""


def _safe_trace(
    *,
    response: LLMResponse,
    provider: str,
    model: str,
    prompt_version: str,
    input_text: str,
    output_text: str,
    parse_error: str | None,
    sanitized_preview: str,
    stage: str,
    chunk_index: int | None,
    retried: bool,
) -> dict[str, Any]:
    trace: dict[str, Any] = {
        "provider": response.provider or provider,
        "model": response.model or model,
        "prompt_version": prompt_version,
        "finish_reason": response.finish_reason,
        "usage": {
            "input_tokens": response.usage.input_tokens,
            "output_tokens": response.usage.output_tokens,
        },
        "input_char_count": len(input_text),
        "output_char_count": len(output_text),
        "input_preview": input_text[:280],
        "output_preview": output_text[:480],
        "sanitized_preview": sanitized_preview[:480],
        "stage": stage,
        "retried": retried,
    }
    if parse_error:
        trace["parse_error"] = parse_error
    if chunk_index is not None:
        trace["chunk_index"] = chunk_index
    return trace


class OpenDomainLLMExtractor:
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

    def classify_document_domain(self, document: OntologyDocument) -> str:
        return "pending"

    def extract_ontology_candidates(
        self,
        document: OntologyDocument,
        workspace_id: str | None = None,
        provider: str | None = None,
        model: str | None = None,
    ) -> ExtractionResult:
        if not self._settings.ontology_llm_enabled:
            return ExtractionResult(domain="disabled", entities=[], relations=[])
        if not document.markdown.strip():
            return ExtractionResult(domain="general", entities=[], relations=[])
        if not provider or not model:
            return ExtractionResult(domain="unconfigured", entities=[], relations=[])
        if not self._model_config_service.is_ready(provider, model, workspace_id):
            return ExtractionResult(domain="unavailable", entities=[], relations=[])

        text = document.markdown[: self._settings.ontology_markdown_char_limit]
        schema = self._schema_registry.for_workspace(workspace_id or self._settings.default_workspace_id)
        chunks = chunk_for_extraction(
            text,
            window=6000,
            overlap=500,
            max_chunks=self._settings.ontology_extraction_max_chunks,
        )
        merged_entities: dict[str, ExtractedEntity] = {}
        merged_relations: dict[tuple[str, str, str], ExtractedRelation] = {}
        domains: list[str] = []
        traces: list[dict[str, Any]] = []
        errors: list[str] = []

        for idx, chunk in enumerate(chunks):
            entities_payload, entity_trace = self._extract_entities(chunk, idx, provider, model, schema.entity_types)
            traces.append(entity_trace)
            if isinstance(entity_trace.get("parse_error"), str):
                errors.append(f"chunk[{idx}] entities: {entity_trace['parse_error']}")
            if entities_payload.domain not in {"", "general", "pending"}:
                domains.append(entities_payload.domain)
            for raw in entities_payload.entities:
                self._merge_entity(
                    merged_entities,
                    self._to_domain_entity(raw, document=document, provider=provider, model=model),
                )

            if len(merged_entities) < 2:
                continue
            relation_payload, relation_trace = self._extract_relations(
                chunk, idx, provider, model, schema.relation_types, list(merged_entities.values())
            )
            traces.append(relation_trace)
            if isinstance(relation_trace.get("parse_error"), str):
                errors.append(f"chunk[{idx}] relations: {relation_trace['parse_error']}")
            for raw in relation_payload.relations:
                self._merge_relation(
                    merged_relations,
                    self._to_domain_relation(raw, document=document, provider=provider, model=model),
                )

        domain = Counter(domains).most_common(1)[0][0] if domains else "general"
        return ExtractionResult(
            domain=domain,
            entities=list(merged_entities.values()),
            relations=list(merged_relations.values()),
            trace={"chunks": traces, "errors": errors},
        )

    def summarize_ontology(
        self,
        document: OntologyDocument,
        *,
        workspace_id: str | None = None,
        provider: str | None = None,
        model: str | None = None,
        domain: str | None = None,
    ) -> OntologyNarrative:
        if not document.markdown.strip():
            return OntologyNarrative(title="Ontology", summary="")
        if (
            not self._settings.ontology_llm_enabled
            or not provider
            or not model
            or not self._model_config_service.is_ready(provider, model, workspace_id or self._settings.default_workspace_id)
        ):
            return self._fallback_narrative(document, domain=domain)

        text = document.markdown[: self._settings.ontology_markdown_char_limit]
        system_prompt, user_prompt = build_summary_prompt(text=text, domain=domain or "general")
        payload, _trace = self._invoke_json(provider, model, system_prompt, user_prompt, text, "summary", None)
        if payload is None:
            return self._fallback_narrative(document, domain=domain)
        try:
            narrative = _LLMOntologyNarrative.model_validate(payload)
        except ValidationError:
            return self._fallback_narrative(document, domain=domain)
        return OntologyNarrative(
            title=((narrative.title or "").strip() or "Ontology")[:120],
            summary=((narrative.summary or "").strip())[:280],
        )

    def _extract_entities(
        self, chunk: str, chunk_index: int, provider: str, model: str, known_entity_types: list[str]
    ) -> tuple[_LLMEntityExtraction, dict[str, Any]]:
        system_prompt, user_prompt = build_entity_extraction_prompt(
            text=chunk, known_entity_types=known_entity_types, prompt_version=self._settings.ontology_prompt_version
        )
        payload, trace = self._invoke_json(provider, model, system_prompt, user_prompt, chunk, "entities", chunk_index)
        if payload is None:
            return _LLMEntityExtraction(), trace
        try:
            return _LLMEntityExtraction.model_validate(payload), trace
        except ValidationError as exc:
            trace["parse_error"] = f"entity_validation_error: {exc.errors()[0]['type']}"
            return _LLMEntityExtraction(), trace

    def _extract_relations(
        self,
        chunk: str,
        chunk_index: int,
        provider: str,
        model: str,
        known_relation_types: list[str],
        entities: list[ExtractedEntity],
    ) -> tuple[_LLMRelationExtraction, dict[str, Any]]:
        whitelist = [f"{entity.resolution_key} | {entity.canonical_name}" for entity in entities]
        system_prompt, user_prompt = build_relation_extraction_prompt(
            text=chunk,
            entity_whitelist=whitelist,
            known_relation_types=known_relation_types,
            prompt_version=self._settings.ontology_prompt_version,
        )
        payload, trace = self._invoke_json(provider, model, system_prompt, user_prompt, chunk, "relations", chunk_index)
        if payload is None:
            return _LLMRelationExtraction(), trace
        try:
            return _LLMRelationExtraction.model_validate(payload), trace
        except ValidationError as exc:
            trace["parse_error"] = f"relation_validation_error: {exc.errors()[0]['type']}"
            return _LLMRelationExtraction(), trace

    def _invoke_json(
        self,
        provider: str,
        model: str,
        system_prompt: str,
        user_prompt: str,
        input_text: str,
        stage: str,
        chunk_index: int | None,
    ) -> tuple[dict[str, Any] | None, dict[str, Any]]:
        payload, response = self._invoke_model(provider, model, system_prompt, user_prompt, self._settings.ontology_extraction_max_tokens)
        parsed, parse_error = parse_llm_json(payload)
        trace = _safe_trace(
            response=response,
            provider=provider,
            model=model,
            prompt_version=self._settings.ontology_prompt_version,
            input_text=input_text,
            output_text=payload,
            parse_error=parse_error,
            sanitized_preview=sanitize_llm_json_payload(payload),
            stage=stage,
            chunk_index=chunk_index,
            retried=False,
        )
        if parsed is not None and response.finish_reason != "max_tokens":
            return parsed, trace

        retry_payload, retry_response = self._invoke_model(
            provider,
            model,
            system_prompt,
            f"{user_prompt}\n\nThe previous response was truncated or invalid. Respond with ONLY minimal valid JSON.",
            int(self._settings.ontology_extraction_max_tokens * 1.5),
        )
        retry_parsed, retry_error = parse_llm_json(retry_payload)
        retry_trace = _safe_trace(
            response=retry_response,
            provider=provider,
            model=model,
            prompt_version=self._settings.ontology_prompt_version,
            input_text=input_text,
            output_text=retry_payload,
            parse_error=f"{parse_error}; retry={retry_error}" if parse_error and retry_error else retry_error,
            sanitized_preview=sanitize_llm_json_payload(retry_payload),
            stage=stage,
            chunk_index=chunk_index,
            retried=True,
        )
        if retry_parsed is not None:
            return retry_parsed, retry_trace
        if parsed is not None:
            retry_trace["parse_error"] = (
                f"{retry_trace.get('parse_error')}; using_initial_payload"
                if retry_trace.get("parse_error")
                else "using_initial_payload"
            )
            return parsed, retry_trace
        return None, retry_trace

    def _invoke_model(
        self, provider: str, model: str, system_prompt: str, user_prompt: str, max_tokens: int
    ) -> tuple[str, LLMResponse]:
        adapter = self._adapter_registry.get(provider)
        if adapter is None:
            return "", LLMResponse(content=None, provider=provider, model=model)
        response = adapter.run(
            messages=[LLMMessage(role="user", content=user_prompt)],
            tools=(),
            tool_choice="none",
            system=system_prompt,
            model=model,
            max_tokens=max_tokens,
            temperature=0,
            response_format="json_object",
            reasoning_effort=self._reasoning_effort(),
        )
        return (response.content or "").strip(), response

    def _reasoning_effort(self) -> Literal["low", "medium", "high"] | None:
        value = (self._settings.ontology_extraction_reasoning_effort or "").lower()
        return value if value in {"low", "medium", "high"} else None

    def _to_domain_entity(self, item: _LLMEntity, *, document: OntologyDocument, provider: str, model: str) -> ExtractedEntity:
        return ExtractedEntity(
            name=item.name,
            canonical_name=item.canonical_name,
            resolution_key=item.resolution_key,
            entity_type=item.entity_type,
            confidence=max(0.0, min(1.0, float(item.confidence))),
            source_chunk_id=None,
            evidence_text=item.evidence_text,
            provenance={"extractor": "open_domain_llm", "provider": provider, "model": model, "prompt_version": self._settings.ontology_prompt_version, "source_document_id": document.document_id},
            aliases=set(item.aliases),
            query_rules=self._normalize_query_rules(item.query_rules),
            facts=self._normalize_facts(item.facts),
        )

    def _to_domain_relation(self, item: _LLMRelation, *, document: OntologyDocument, provider: str, model: str) -> ExtractedRelation:
        return ExtractedRelation(
            source_resolution_key=item.source_resolution_key,
            target_resolution_key=item.target_resolution_key,
            source_name=item.source_name,
            target_name=item.target_name,
            relation_type=item.relation_type,
            confidence=max(0.0, min(1.0, float(item.confidence))),
            source_chunk_id=None,
            evidence_text=item.evidence_text,
            provenance={"extractor": "open_domain_llm", "provider": provider, "model": model, "prompt_version": self._settings.ontology_prompt_version, "source_document_id": document.document_id},
            query_rules=self._normalize_query_rules(item.query_rules),
            facts=self._normalize_facts(item.facts),
        )

    @staticmethod
    def _normalize_query_rules(items: list[dict[str, Any]]) -> list[QueryRuleSpec]:
        normalized: list[QueryRuleSpec] = []
        for item in items or []:
            if not isinstance(item, dict):
                continue
            route = str(item.get("query_route") or "").strip().lower()
            if route not in {"graph", "sql_facts", "hybrid"}:
                continue
            scope = str(item.get("scope") or "entity_type").strip()
            rule_id = str(item.get("rule_id") or "").strip() or f"rule:{scope}:{route}:{len(normalized)+1}"
            normalized.append(
                QueryRuleSpec(
                    rule_id=rule_id,
                    scope=scope,
                    query_route=route,
                    trigger_keywords=[str(x) for x in item.get("trigger_keywords", []) if str(x).strip()],
                    intent_tags=[str(x) for x in item.get("intent_tags", []) if str(x).strip()],
                    required_fields=[str(x) for x in item.get("required_fields", []) if str(x).strip()],
                    aggregation=str(item.get("aggregation") or "latest"),
                    confidence_threshold=item.get("confidence_threshold"),
                    fallback_route=item.get("fallback_route"),
                    metadata=item.get("metadata") if isinstance(item.get("metadata"), dict) else {},
                )
            )
        return normalized

    @staticmethod
    def _normalize_facts(items: list[dict[str, Any]]) -> list[ExtractedFact]:
        normalized: list[ExtractedFact] = []
        for item in items or []:
            if not isinstance(item, dict):
                continue
            metric_key = str(item.get("metric_key") or "").strip()
            if not metric_key:
                continue
            normalized.append(
                ExtractedFact(
                    metric_key=metric_key,
                    value_num=item.get("value_num"),
                    value_text=item.get("value_text"),
                    value_bool=item.get("value_bool"),
                    unit=item.get("unit"),
                    observed_at=item.get("observed_at"),
                    source_chunk_id=item.get("source_chunk_id"),
                    metadata=item.get("metadata") if isinstance(item.get("metadata"), dict) else {},
                )
            )
        return normalized

    @staticmethod
    def _merge_entity(target: dict[str, ExtractedEntity], entity: ExtractedEntity) -> None:
        key = entity.resolution_key.strip().lower() or entity.canonical_name.strip().lower()
        if not key:
            return
        existing = target.get(key)
        if existing is None:
            target[key] = entity
            return
        existing.aliases |= entity.aliases
        if entity.confidence > existing.confidence:
            existing.name = entity.name
            existing.canonical_name = entity.canonical_name
            existing.resolution_key = entity.resolution_key
            existing.entity_type = entity.entity_type
            existing.confidence = entity.confidence
            existing.evidence_text = entity.evidence_text

    @staticmethod
    def _merge_relation(target: dict[tuple[str, str, str], ExtractedRelation], relation: ExtractedRelation) -> None:
        key = (
            relation.source_resolution_key.strip().lower(),
            relation.relation_type.strip().lower(),
            relation.target_resolution_key.strip().lower(),
        )
        if not all(key):
            return
        existing = target.get(key)
        if existing is None:
            target[key] = relation
        elif relation.confidence > existing.confidence:
            existing.source_name = relation.source_name
            existing.target_name = relation.target_name
            existing.confidence = relation.confidence
            existing.evidence_text = relation.evidence_text

    @staticmethod
    def _fallback_narrative(document: OntologyDocument, *, domain: str | None = None) -> OntologyNarrative:
        text = document.markdown[:600].strip()
        words = [word.strip(".,:;!?()[]{}\"'") for word in text.split()]
        title = " ".join(word for word in words[:5] if word) or "Ontology"
        if domain and domain not in {"general", "pending"}:
            title = f"{domain.replace('_', ' ').title()} Ontology"
        return OntologyNarrative(title=title[:120], summary=text[:280])
