from __future__ import annotations

from semantic_reasoning_agent.db.models import DocumentChunkORM
from semantic_reasoning_agent.domain.ontology.models import (
    ExtractedEntity,
    ExtractedRelation,
    ExtractionResult,
)
from semantic_reasoning_agent.domain.ontology.scoring import combine_confidence
from semantic_reasoning_agent.infrastructure.ontology.llm_extractor import LLMStructuredExtractor
from semantic_reasoning_agent.infrastructure.ontology.rule_extractor import RuleSeedExtractor


class HybridOntologyExtractor:
    def __init__(self, llm_extractor: LLMStructuredExtractor, rule_extractor: RuleSeedExtractor) -> None:
        self._llm_extractor = llm_extractor
        self._rule_extractor = rule_extractor

    def classify_document_domain(self, chunks: list[DocumentChunkORM]) -> str:
        return self._rule_extractor.classify_document_domain(chunks)

    def extract_ontology_candidates(self, chunks: list[DocumentChunkORM]) -> ExtractionResult:
        rule_result = self._rule_extractor.extract_ontology_candidates(chunks)
        llm_result = self._llm_extractor.extract_ontology_candidates(chunks)
        domain = llm_result.domain or rule_result.domain

        entities = self._merge_entities(rule_result.entities, llm_result.entities)
        relations = self._merge_relations(rule_result.relations, llm_result.relations)
        return ExtractionResult(domain=domain, entities=entities, relations=relations)

    def _merge_entities(
        self,
        rule_entities: list[ExtractedEntity],
        llm_entities: list[ExtractedEntity],
    ) -> list[ExtractedEntity]:
        by_key: dict[str, ExtractedEntity] = {entity.resolution_key: entity for entity in rule_entities}
        for llm_entity in llm_entities:
            existing = by_key.get(llm_entity.resolution_key)
            if existing is None:
                by_key[llm_entity.resolution_key] = llm_entity
                continue
            merged_aliases = set(existing.aliases).union(llm_entity.aliases)
            combined = combine_confidence(
                rule_score=existing.confidence,
                llm_score=llm_entity.confidence,
                evidence_count=2,
                ontology_match_score=0.5,
            )
            by_key[llm_entity.resolution_key] = ExtractedEntity(
                name=existing.name,
                canonical_name=existing.canonical_name,
                resolution_key=existing.resolution_key,
                entity_type=llm_entity.entity_type or existing.entity_type,
                confidence=combined,
                source_chunk_id=existing.source_chunk_id or llm_entity.source_chunk_id,
                evidence_text=existing.evidence_text,
                provenance={
                    "extractor": "hybrid",
                    "rule": existing.provenance,
                    "llm": llm_entity.provenance,
                },
                aliases=merged_aliases,
            )
        return sorted(by_key.values(), key=lambda item: item.canonical_name.lower())

    def _merge_relations(
        self,
        rule_relations: list[ExtractedRelation],
        llm_relations: list[ExtractedRelation],
    ) -> list[ExtractedRelation]:
        by_key: dict[tuple[str, str, str], ExtractedRelation] = {
            (rel.source_resolution_key, rel.target_resolution_key, rel.relation_type): rel
            for rel in rule_relations
        }
        for llm_relation in llm_relations:
            key = (
                llm_relation.source_resolution_key,
                llm_relation.target_resolution_key,
                llm_relation.relation_type,
            )
            existing = by_key.get(key)
            if existing is None:
                by_key[key] = llm_relation
                continue
            by_key[key] = ExtractedRelation(
                source_resolution_key=existing.source_resolution_key,
                target_resolution_key=existing.target_resolution_key,
                source_name=existing.source_name,
                target_name=existing.target_name,
                relation_type=existing.relation_type,
                confidence=combine_confidence(
                    rule_score=existing.confidence,
                    llm_score=llm_relation.confidence,
                    evidence_count=2,
                    ontology_match_score=0.5,
                ),
                source_chunk_id=existing.source_chunk_id or llm_relation.source_chunk_id,
                evidence_text=existing.evidence_text,
                provenance={
                    "extractor": "hybrid",
                    "rule": existing.provenance,
                    "llm": llm_relation.provenance,
                },
            )
        return sorted(
            by_key.values(),
            key=lambda item: (item.relation_type, item.source_name.lower(), item.target_name.lower()),
        )
