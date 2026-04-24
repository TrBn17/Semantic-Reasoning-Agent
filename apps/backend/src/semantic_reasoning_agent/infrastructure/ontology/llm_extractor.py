from __future__ import annotations

from collections import Counter
import re
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


def _is_ontology_input_context_exceeded_error(exc: BaseException) -> bool:
    """True if the provider rejected the call because the prompt / context was too large."""
    try:
        text = f"{type(exc).__name__} {exc!s}".lower()
    except Exception:  # noqa: BLE001
        return False
    markers = (
        "context length",
        "context_length",
        "maximum context",
        "max_tokens",
        "token limit",
        "too many tokens",
        "string too long",
        "string_too_long",
        "reduce the length of the",
        "input is too long",
    )
    if any(m in text for m in markers):
        return True
    if " 400" in text or " error 400" in text:
        if "token" in text or "context" in text or "length" in text:
            return True
    return False


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
    _FULL_PASS_MAX_INPUT_TOKENS = 256_000
    _FALLBACK_CHUNK_MAX_DOCUMENT_TOKENS = 32_768
    _CHUNK_OVERLAP_TOKENS = 512
    _TOKEN_ENCODING = "cl100k_base"
    _CHARS_PER_TOKEN_FALLBACK = 4.0
    _LEGACY_CHUNK_WINDOW_CHARS = 6000
    _LEGACY_CHUNK_OVERLAP_CHARS = 500

    _UUID_PATTERN = re.compile(
        r"^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$",
        re.IGNORECASE,
    )
    _HEXISH_PATTERN = re.compile(r"^[0-9a-f_-]{20,}$", re.IGNORECASE)

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

    def _count_tokens(self, text: str) -> int:
        try:
            import tiktoken

            enc = tiktoken.get_encoding(self._TOKEN_ENCODING)
            return len(enc.encode(text))
        except Exception:
            return max(1, int(len(text) / self._CHARS_PER_TOKEN_FALLBACK + 0.5))

    def _split_by_tokens(self, text: str, *, max_tokens: int) -> list[str]:
        try:
            import tiktoken

            normalized = text.strip()
            if not normalized:
                return []
            enc = tiktoken.get_encoding(self._TOKEN_ENCODING)
            token_ids = enc.encode(normalized)
            if len(token_ids) <= max_tokens:
                return [normalized]
            step = max(1, max_tokens - self._CHUNK_OVERLAP_TOKENS)
            chunks: list[str] = []
            start = 0
            while start < len(token_ids) and len(chunks) < self._settings.ontology_extraction_max_chunks:
                end = min(len(token_ids), start + max_tokens)
                segment = enc.decode(token_ids[start:end]).strip()
                if segment:
                    chunks.append(segment)
                if end >= len(token_ids):
                    break
                start += step
            return chunks
        except Exception:
            return chunk_for_extraction(
                text,
                window=self._LEGACY_CHUNK_WINDOW_CHARS,
                overlap=self._LEGACY_CHUNK_OVERLAP_CHARS,
                max_chunks=self._settings.ontology_extraction_max_chunks,
            )

    @staticmethod
    def _with_large_document_note(chunk: str, idx: int, total: int) -> str:
        if total <= 1:
            return chunk
        note = (
            "NOTE: The source document is large and has been split into chunks. "
            f"You are processing chunk {idx + 1}/{total}. "
            "Extract grounded entities/relations from this chunk and keep resolution keys stable across chunks."
        )
        return f"{note}\n\n{chunk}"

    def classify_document_domain(self, document: OntologyDocument) -> str:
        return self._settings.ontology_classify_deferred_token

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
        document_token_count = self._count_tokens(text)
        full_pass = document_token_count <= self._FULL_PASS_MAX_INPUT_TOKENS
        entity_segments = [text] if full_pass else self._split_by_tokens(
            text,
            max_tokens=self._FALLBACK_CHUNK_MAX_DOCUMENT_TOKENS,
        )
        if not entity_segments:
            entity_segments = [text]

        merged_entities: dict[str, ExtractedEntity] = {}
        merged_relations: dict[tuple[str, str, str], ExtractedRelation] = {}
        domains: list[str] = []
        traces: list[dict[str, Any]] = []
        errors: list[str] = []
        raw_entity_rows_from_llm = 0
        raw_relation_rows_from_llm = 0

        entity_retried = False
        entity_note_mode = not full_pass
        while True:
            for idx, raw_chunk in enumerate(entity_segments):
                chunk = self._with_large_document_note(raw_chunk, idx, len(entity_segments)) if entity_note_mode else raw_chunk
                try:
                    entities_payload, entity_trace = self._extract_entities(
                        chunk, idx, provider, model, schema.entity_types
                    )
                except Exception as exc:
                    if (
                        not entity_retried
                        and idx == 0
                        and len(entity_segments) == 1
                        and _is_ontology_input_context_exceeded_error(exc)
                    ):
                        entity_retried = True
                        errors.append(
                            f"entity_segment[0] context/length; retrying with token chunks: {exc!s}"
                        )
                        entity_segments = self._split_by_tokens(
                            text,
                            max_tokens=self._FALLBACK_CHUNK_MAX_DOCUMENT_TOKENS,
                        )
                        if not entity_segments:
                            entity_segments = [text]
                        entity_note_mode = len(entity_segments) > 1
                        merged_entities = {}
                        domains = []
                        traces = []
                        break
                    raise
                traces.append(entity_trace)
                if isinstance(entity_trace.get("parse_error"), str):
                    errors.append(f"entity_segment[{idx}] entities: {entity_trace['parse_error']}")
                if entities_payload.domain not in frozenset(
                    {
                        "",
                        "general",
                        "pending",
                        (self._settings.ontology_classify_deferred_token or "").strip() or "pending",
                    }
                ):
                    domains.append(entities_payload.domain)
                raw_entity_rows_from_llm += len(entities_payload.entities)
                for raw in entities_payload.entities:
                    self._merge_entity(
                        merged_entities,
                        self._to_domain_entity(raw, document=document, provider=provider, model=model),
                    )
            else:
                break

        if len(merged_entities) < 2:
            domain = Counter(domains).most_common(1)[0][0] if domains else "general"
            canonical_entities = len(merged_entities)
            merge_stats: dict[str, Any] = {
                "raw_entity_rows_from_llm": raw_entity_rows_from_llm,
                "canonical_entities_after_merge": canonical_entities,
                "raw_relation_rows_from_llm": 0,
                "canonical_relations_after_merge": 0,
                "entity_dedup_savings": max(0, raw_entity_rows_from_llm - canonical_entities),
                "resolution_rule": (
                    "Entities with the same resolution_key (case-insensitive; fallback canonical_name) "
                    "are merged across chunks: aliases union, higher confidence wins for name/type/evidence."
                ),
            }
            return ExtractionResult(
                domain=domain,
                entities=list(merged_entities.values()),
                relations=[],
                trace={
                    "chunks": traces,
                    "errors": errors,
                    "merge_stats": merge_stats,
                    "chunking": {
                        "document_token_count": document_token_count,
                        "full_pass_token_threshold": self._FULL_PASS_MAX_INPUT_TOKENS,
                        "entity_segment_count": len(entity_segments),
                        "entity_mode": "chunked" if len(entity_segments) > 1 else "full",
                    },
                },
            )

        relation_segments = [text] if full_pass else self._split_by_tokens(
            text,
            max_tokens=self._FALLBACK_CHUNK_MAX_DOCUMENT_TOKENS,
        )
        if not relation_segments:
            relation_segments = [text]
        entity_values = list(merged_entities.values())
        relation_retried = False
        relation_note_mode = not full_pass
        while True:
            for idx, raw_chunk in enumerate(relation_segments):
                chunk = self._with_large_document_note(raw_chunk, idx, len(relation_segments)) if relation_note_mode else raw_chunk
                try:
                    relation_payload, relation_trace = self._extract_relations(
                        chunk, idx, provider, model, schema.relation_types, entity_values
                    )
                except Exception as exc:
                    if (
                        not relation_retried
                        and idx == 0
                        and len(relation_segments) == 1
                        and _is_ontology_input_context_exceeded_error(exc)
                    ):
                        relation_retried = True
                        errors.append(
                            f"relation_segment[0] context/length; retrying with token chunks: {exc!s}"
                        )
                        relation_segments = self._split_by_tokens(
                            text,
                            max_tokens=self._FALLBACK_CHUNK_MAX_DOCUMENT_TOKENS,
                        )
                        if not relation_segments:
                            relation_segments = [text]
                        relation_note_mode = len(relation_segments) > 1
                        merged_relations = {}
                        break
                    raise
                traces.append(relation_trace)
                if isinstance(relation_trace.get("parse_error"), str):
                    errors.append(f"relation_segment[{idx}] relations: {relation_trace['parse_error']}")
                raw_relation_rows_from_llm += len(relation_payload.relations)
                for raw in relation_payload.relations:
                    self._merge_relation(
                        merged_relations,
                        self._to_domain_relation(raw, document=document, provider=provider, model=model),
                    )
            else:
                break

        domain = Counter(domains).most_common(1)[0][0] if domains else "general"
        canonical_e = len(merged_entities)
        canonical_r = len(merged_relations)
        merge_stats_full: dict[str, Any] = {
            "raw_entity_rows_from_llm": raw_entity_rows_from_llm,
            "canonical_entities_after_merge": canonical_e,
            "raw_relation_rows_from_llm": raw_relation_rows_from_llm,
            "canonical_relations_after_merge": canonical_r,
            "entity_dedup_savings": max(0, raw_entity_rows_from_llm - canonical_e),
            "relation_dedup_savings": max(0, raw_relation_rows_from_llm - canonical_r),
            "resolution_rule": (
                "Entities: merge by resolution_key across chunks (aliases union, best confidence wins). "
                "Relations: merge by (source_resolution_key, relation_type, target_resolution_key)."
            ),
        }
        return ExtractionResult(
            domain=domain,
            entities=list(merged_entities.values()),
            relations=list(merged_relations.values()),
            trace={
                "chunks": traces,
                "errors": errors,
                "merge_stats": merge_stats_full,
                "chunking": {
                    "document_token_count": document_token_count,
                    "full_pass_token_threshold": self._FULL_PASS_MAX_INPUT_TOKENS,
                    "entity_segment_count": len(entity_segments),
                    "relation_segment_count": len(relation_segments),
                    "entity_mode": "chunked" if len(entity_segments) > 1 else "full",
                    "relation_mode": "chunked" if len(relation_segments) > 1 else "full",
                },
            },
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
        resolved_title = self._normalize_narrative_title(narrative.title, domain=domain)
        return OntologyNarrative(
            title=resolved_title[:120],
            summary=((narrative.summary or "").strip())[:280],
        )

    def _extract_entities(
        self, chunk: str, chunk_index: int, provider: str, model: str, known_entity_types: list[str]
    ) -> tuple[_LLMEntityExtraction, dict[str, Any]]:
        system_prompt, user_prompt = build_entity_extraction_prompt(
            text=chunk,
            known_entity_types=known_entity_types,
            prompt_version=self._settings.ontology_prompt_version,
            entity_count_min=self._settings.ontology_extraction_entity_count_min,
            entity_count_max=self._settings.ontology_extraction_entity_count_max,
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
            route = str(item.get("query_route") or "").strip().lower() or "hybrid"
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
                    fallback_route=(
                        str(item.get("fallback_route")).strip().lower()
                        if str(item.get("fallback_route") or "").strip()
                        else None
                    ),
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
                metric_key = f"fact_{len(normalized) + 1}"
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
        existing.query_rules = OpenDomainLLMExtractor._merge_query_rules(existing.query_rules, entity.query_rules)
        existing.facts = OpenDomainLLMExtractor._merge_facts(existing.facts, entity.facts)
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
            return
        existing.query_rules = OpenDomainLLMExtractor._merge_query_rules(existing.query_rules, relation.query_rules)
        existing.facts = OpenDomainLLMExtractor._merge_facts(existing.facts, relation.facts)
        if relation.confidence > existing.confidence:
            existing.source_name = relation.source_name
            existing.target_name = relation.target_name
            existing.confidence = relation.confidence
            existing.evidence_text = relation.evidence_text

    @staticmethod
    def _merge_query_rules(existing: list[QueryRuleSpec], incoming: list[QueryRuleSpec]) -> list[QueryRuleSpec]:
        merged: list[QueryRuleSpec] = []
        seen: set[tuple[str, str, str]] = set()
        for rule in [*(existing or []), *(incoming or [])]:
            key = (str(rule.rule_id).strip(), str(rule.scope).strip(), str(rule.query_route).strip())
            if not all(key) or key in seen:
                continue
            seen.add(key)
            merged.append(rule)
        return merged

    @staticmethod
    def _merge_facts(existing: list[ExtractedFact], incoming: list[ExtractedFact]) -> list[ExtractedFact]:
        merged: list[ExtractedFact] = []
        seen: set[tuple[str, Any, Any, Any, Any, Any]] = set()
        for fact in [*(existing or []), *(incoming or [])]:
            key = (
                str(fact.metric_key).strip(),
                fact.value_num,
                fact.value_text,
                fact.value_bool,
                fact.unit,
                fact.observed_at,
            )
            if not key[0] or key in seen:
                continue
            seen.add(key)
            merged.append(fact)
        return merged

    @staticmethod
    def _fallback_narrative(document: OntologyDocument, *, domain: str | None = None) -> OntologyNarrative:
        text = document.markdown[:600].strip()
        words = [word.strip(".,:;!?()[]{}\"'") for word in text.split()]
        title = " ".join(word for word in words[:5] if word) or "Ontology"
        title = OpenDomainLLMExtractor._normalize_narrative_title(title, domain=domain)
        return OntologyNarrative(title=title[:120], summary=text[:280])

    @classmethod
    def _normalize_narrative_title(cls, title: str | None, *, domain: str | None = None) -> str:
        normalized = (title or "").strip()
        domain_title = (
            f"{domain.replace('_', ' ').title()} Ontology"
            if domain and domain not in {"general", "pending"}
            else "Ontology"
        )
        if not normalized:
            return domain_title
        if cls._looks_like_identifier_title(normalized):
            return domain_title
        return normalized

    @classmethod
    def _looks_like_identifier_title(cls, title: str) -> bool:
        compact = title.strip()
        if cls._UUID_PATTERN.fullmatch(compact):
            return True
        if " " not in compact and cls._HEXISH_PATTERN.fullmatch(compact):
            return True
        return False
