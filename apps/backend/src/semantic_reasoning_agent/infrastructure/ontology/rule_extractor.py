from __future__ import annotations

import re
from typing import Any

from semantic_reasoning_agent.db.models import DocumentChunkORM
from semantic_reasoning_agent.domain.ontology.models import (
    ExtractedEntity,
    ExtractedRelation,
    ExtractionResult,
)

RELATION_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    (
        "depends_on",
        re.compile(
            r"(?P<source>[A-Za-z][A-Za-z0-9/&()' -]{1,80}?)\s+depends on\s+"
            r"(?P<target>[A-Za-z][A-Za-z0-9/&()' -]{1,80}?)(?:[.;,]|$)",
            re.IGNORECASE,
        ),
    ),
    (
        "requires",
        re.compile(
            r"(?P<source>[A-Za-z][A-Za-z0-9/&()' -]{1,80}?)\s+requires\s+"
            r"(?P<target>[A-Za-z][A-Za-z0-9/&()' -]{1,80}?)(?:[.;,]|$)",
            re.IGNORECASE,
        ),
    ),
    (
        "uses",
        re.compile(
            r"(?P<source>[A-Za-z][A-Za-z0-9/&()' -]{1,80}?)\s+uses\s+"
            r"(?P<target>[A-Za-z][A-Za-z0-9/&()' -]{1,80}?)(?:[.;,]|$)",
            re.IGNORECASE,
        ),
    ),
    (
        "integrates_with",
        re.compile(
            r"(?P<source>[A-Za-z][A-Za-z0-9/&()' -]{1,80}?)\s+integrates with\s+"
            r"(?P<target>[A-Za-z][A-Za-z0-9/&()' -]{1,80}?)(?:[.;,]|$)",
            re.IGNORECASE,
        ),
    ),
]

DOMAIN_KEYWORDS = {
    "technology": {"system", "service", "platform", "api", "database", "pipeline"},
    "compliance": {"approval", "audit", "control", "policy", "risk", "governance"},
    "finance": {"revenue", "budget", "sales", "invoice", "margin", "forecast"},
    "operations": {"delivery", "workflow", "support", "incident", "handoff", "runbook"},
}

ENTITY_FALLBACK_PATTERN = re.compile(
    r"\b([A-Z][A-Za-z0-9]+(?:\s+[A-Za-z][A-Za-z0-9/&()'-]+){0,3})\b"
)
WORD_PATTERN = re.compile(r"[A-Za-z0-9]+")
SENTENCE_SPLIT_PATTERN = re.compile(r"(?<=[.!?])\s+|\n+")


class RuleSeedExtractor:
    def classify_document_domain(self, chunks: list[DocumentChunkORM]) -> str:
        combined_text = "\n".join(chunk.text for chunk in chunks)
        return _classify_domain(combined_text)

    def extract_ontology_candidates(self, chunks: list[DocumentChunkORM]) -> ExtractionResult:
        entities_by_key: dict[str, ExtractedEntity] = {}
        relations_by_key: dict[tuple[str, str, str], ExtractedRelation] = {}

        for chunk in chunks:
            for sentence in _split_sentences(chunk.text):
                provenance = _build_provenance(chunk)
                matched_relation = False
                for relation_type, pattern in RELATION_PATTERNS:
                    for match in pattern.finditer(sentence):
                        source_name = _clean_entity_phrase(match.group("source"))
                        target_name = _clean_entity_phrase(match.group("target"))
                        if not _is_valid_entity_name(source_name) or not _is_valid_entity_name(target_name):
                            continue
                        matched_relation = True
                        source_entity = _upsert_entity(
                            entities_by_key,
                            source_name,
                            sentence,
                            provenance,
                            chunk.chunk_id,
                        )
                        target_entity = _upsert_entity(
                            entities_by_key,
                            target_name,
                            sentence,
                            provenance,
                            chunk.chunk_id,
                        )
                        relation_key = (
                            source_entity.resolution_key,
                            target_entity.resolution_key,
                            relation_type,
                        )
                        existing_relation = relations_by_key.get(relation_key)
                        confidence = 0.72
                        if existing_relation is None or confidence > existing_relation.confidence:
                            relations_by_key[relation_key] = ExtractedRelation(
                                source_resolution_key=source_entity.resolution_key,
                                target_resolution_key=target_entity.resolution_key,
                                source_name=source_entity.canonical_name,
                                target_name=target_entity.canonical_name,
                                relation_type=relation_type,
                                confidence=confidence,
                                source_chunk_id=chunk.chunk_id,
                                evidence_text=sentence,
                                provenance=provenance,
                            )
                if matched_relation:
                    continue
                for phrase in _extract_fallback_entity_phrases(sentence):
                    _upsert_entity(
                        entities_by_key,
                        phrase,
                        sentence,
                        provenance,
                        chunk.chunk_id,
                        confidence=0.56,
                    )

        return ExtractionResult(
            domain=self.classify_document_domain(chunks),
            entities=sorted(entities_by_key.values(), key=lambda item: item.canonical_name.lower()),
            relations=sorted(
                relations_by_key.values(),
                key=lambda item: (item.relation_type, item.source_name.lower(), item.target_name.lower()),
            ),
        )


def _upsert_entity(
    entities_by_key: dict[str, ExtractedEntity],
    phrase: str,
    evidence_text: str,
    provenance: dict[str, Any],
    source_chunk_id: str | None,
    confidence: float = 0.68,
) -> ExtractedEntity:
    canonical_name = _canonicalize_name(phrase)
    resolution_key = _build_resolution_key(canonical_name)
    entity_type = _infer_entity_type(canonical_name)
    existing = entities_by_key.get(resolution_key)
    if existing is None:
        entity = ExtractedEntity(
            name=canonical_name,
            canonical_name=canonical_name,
            resolution_key=resolution_key,
            entity_type=entity_type,
            confidence=confidence,
            source_chunk_id=source_chunk_id,
            evidence_text=evidence_text,
            provenance=provenance,
            aliases={phrase},
        )
        entities_by_key[resolution_key] = entity
        return entity

    existing.aliases.add(phrase)
    if confidence > existing.confidence:
        existing.confidence = confidence
        existing.entity_type = entity_type
        existing.source_chunk_id = source_chunk_id
        existing.evidence_text = evidence_text
        existing.provenance = provenance
    return existing


def _split_sentences(text: str) -> list[str]:
    parts = [part.strip() for part in SENTENCE_SPLIT_PATTERN.split(text) if part.strip()]
    return parts or [text.strip()]


def _extract_fallback_entity_phrases(sentence: str) -> list[str]:
    phrases: list[str] = []
    for match in ENTITY_FALLBACK_PATTERN.finditer(sentence):
        phrase = _clean_entity_phrase(match.group(1))
        if _is_valid_entity_name(phrase):
            phrases.append(phrase)
    return phrases


def _clean_entity_phrase(value: str) -> str:
    phrase = re.sub(r"\s+", " ", value.strip(" .,:;"))
    phrase = re.sub(r"^(the|a|an)\s+", "", phrase, flags=re.IGNORECASE)
    phrase = re.split(
        r"\s+(for|via|during|under|because)\s+", phrase, maxsplit=1, flags=re.IGNORECASE
    )[0]
    return phrase.strip(" .,:;")


def _canonicalize_name(value: str) -> str:
    words = [token for token in re.split(r"\s+", value.strip()) if token]
    if not words:
        return value.strip()
    normalized: list[str] = []
    for index, word in enumerate(words):
        if index == 0 and word.islower():
            normalized.append(word)
        elif word.isupper():
            normalized.append(word)
        else:
            normalized.append(word[0].upper() + word[1:])
    return " ".join(normalized)


def _build_resolution_key(value: str) -> str:
    tokens = [token.lower() for token in WORD_PATTERN.findall(value)]
    return "-".join(tokens)


def _infer_entity_type(value: str) -> str:
    lowered = value.lower()
    if any(token in lowered for token in ("system", "service", "platform", "api", "database", "pipeline")):
        return "system"
    if any(token in lowered for token in ("initiative", "program", "project", "workstream")):
        return "initiative"
    if any(token in lowered for token in ("team", "department", "group", "office")):
        return "organization"
    if any(token in lowered for token in ("policy", "approval", "control", "requirement")):
        return "policy"
    if any(token in lowered for token in ("dataset", "table", "report", "document", "sheet")):
        return "artifact"
    return "concept"


def _classify_domain(text: str) -> str:
    lowered = text.lower()
    best_domain = "general"
    best_score = 0
    for domain, keywords in DOMAIN_KEYWORDS.items():
        score = sum(lowered.count(keyword) for keyword in keywords)
        if score > best_score:
            best_domain = domain
            best_score = score
    return best_domain


def _is_valid_entity_name(value: str) -> bool:
    tokens = WORD_PATTERN.findall(value)
    if not tokens:
        return False
    if len(tokens) == 1 and tokens[0].lower() in {"it", "this", "that", "they"}:
        return False
    return len(value) >= 3


def _build_provenance(chunk: DocumentChunkORM) -> dict[str, Any]:
    return {
        "document_id": chunk.document_id,
        "chunk_id": chunk.chunk_id,
        "source_url": chunk.source_url,
        "page_number": chunk.page_number,
        "heading_path": chunk.heading_path,
        "sheet_name": chunk.sheet_name,
        "row_start": chunk.row_start,
        "row_end": chunk.row_end,
        "extractor": "rule",
    }
