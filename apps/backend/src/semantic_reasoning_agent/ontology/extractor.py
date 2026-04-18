from semantic_reasoning_agent.domain.ontology.models import (
    ExtractedEntity,
    ExtractedRelation,
    ExtractionResult,
)
from semantic_reasoning_agent.infrastructure.ontology.rule_extractor import RuleSeedExtractor

_rule_extractor = RuleSeedExtractor()


def extract_ontology_candidates(chunks):
    return _rule_extractor.extract_ontology_candidates(chunks)


def classify_document_domain(chunks):
    return _rule_extractor.classify_document_domain(chunks)
