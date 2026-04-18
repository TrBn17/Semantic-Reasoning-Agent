from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


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


@dataclass(slots=True)
class ExtractionResult:
    domain: str
    entities: list[ExtractedEntity]
    relations: list[ExtractedRelation]
