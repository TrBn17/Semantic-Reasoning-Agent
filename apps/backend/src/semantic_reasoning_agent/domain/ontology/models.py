from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class QueryRuleSpec:
    rule_id: str
    scope: str
    query_route: str
    trigger_keywords: list[str] = field(default_factory=list)
    intent_tags: list[str] = field(default_factory=list)
    required_fields: list[str] = field(default_factory=list)
    aggregation: str = "latest"
    confidence_threshold: float | None = None
    fallback_route: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ExtractedFact:
    metric_key: str
    value_num: float | None = None
    value_text: str | None = None
    value_bool: bool | None = None
    unit: str | None = None
    observed_at: str | None = None
    source_chunk_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ExtractedEntity:
    name: str
    canonical_name: str
    resolution_key: str
    entity_type: str
    confidence: float
    source_chunk_id: str | None
    evidence_text: str
    provenance: dict[str, Any]
    aliases: set[str] = field(default_factory=set)
    query_rules: list[QueryRuleSpec] = field(default_factory=list)
    facts: list[ExtractedFact] = field(default_factory=list)


@dataclass(slots=True)
class ExtractedRelation:
    source_resolution_key: str
    target_resolution_key: str
    source_name: str
    target_name: str
    relation_type: str
    confidence: float
    source_chunk_id: str | None
    evidence_text: str
    provenance: dict[str, Any]
    query_rules: list[QueryRuleSpec] = field(default_factory=list)
    facts: list[ExtractedFact] = field(default_factory=list)


@dataclass(slots=True)
class ExtractionResult:
    domain: str
    entities: list[ExtractedEntity]
    relations: list[ExtractedRelation]
    trace: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class OntologyNarrative:
    title: str
    summary: str


@dataclass(slots=True)
class OntologyDocument:
    document_id: str
    markdown: str
