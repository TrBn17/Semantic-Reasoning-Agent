"""SQL / keyword evidence builders for ontology graph search fallbacks."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from semantic_reasoning_agent.domain.contracts.evidence import (
    CitationAnchor,
    Evidence,
    Provenance,
)
from semantic_reasoning_agent.persistence.models import (
    OntologyEntityFactORM,
    OntologyEntityORM,
    OntologyRelationFactORM,
    OntologyRelationORM,
)


def keyword_score(query_lower: str, fields: list[str | None], *, aliases: list[str]) -> float:
    if not query_lower:
        return 0.0
    tokens = [token for token in query_lower.split() if token]
    if not tokens:
        return 0.0
    haystack = " ".join((value or "").lower() for value in fields)
    alias_text = " ".join((alias or "").lower() for alias in aliases)
    full = f"{haystack} {alias_text}".strip()
    if not full:
        return 0.0
    score = 0.0
    for token in tokens:
        if not token:
            continue
        if token in full:
            score += 1.0
    return score


def entity_to_evidence(
    entity: OntologyEntityORM,
    score: float,
    call_id: UUID,
    captured_at: datetime,
) -> Evidence:
    return Evidence(
        evidence_id=uuid4(),
        source_type="graph_node",
        title=entity.name,
        content=f"{entity.name} ({entity.entity_type})",
        citation_anchor=CitationAnchor(
            anchor_type="graph_ref",
            label=entity.entity_type,
            locator=f"ontology-entity:{entity.id}",
        ),
        provenance=Provenance(
            workspace_id=entity.workspace_id,
            source_id=entity.id,
            tool_call_id=call_id,
            captured_at=captured_at,
        ),
        entity_ids=(entity.id,),
        score=float(score),
    )


def relation_to_evidence(
    relation: OntologyRelationORM,
    score: float,
    call_id: UUID,
    captured_at: datetime,
) -> Evidence:
    return Evidence(
        evidence_id=uuid4(),
        source_type="graph_edge",
        title=relation.relation_type,
        content=relation.evidence_text,
        citation_anchor=CitationAnchor(
            anchor_type="graph_ref",
            label=relation.relation_type,
            locator=f"ontology-relation:{relation.id}",
        ),
        provenance=Provenance(
            workspace_id=relation.workspace_id,
            source_id=relation.id,
            tool_call_id=call_id,
            captured_at=captured_at,
        ),
        relation_ids=(relation.id,),
        entity_ids=(relation.source_entity_id, relation.target_entity_id),
        score=float(score),
    )


def entity_fact_to_evidence(
    fact: OntologyEntityFactORM,
    score: float,
    call_id: UUID,
    captured_at: datetime,
) -> Evidence:
    content = f"{fact.metric_key}={fact.value_num if fact.value_num is not None else fact.value_text}"
    if fact.unit:
        content = f"{content} {fact.unit}"
    return Evidence(
        evidence_id=uuid4(),
        source_type="graph_node",
        title=f"Fact: {fact.metric_key}",
        content=content,
        citation_anchor=CitationAnchor(
            anchor_type="graph_ref",
            label="entity_fact",
            locator=f"ontology-entity-fact:{fact.id}",
        ),
        provenance=Provenance(
            workspace_id=fact.workspace_id,
            source_id=fact.id,
            tool_call_id=call_id,
            captured_at=captured_at,
        ),
        entity_ids=(fact.entity_id,),
        score=float(score),
    )


def relation_fact_to_evidence(
    fact: OntologyRelationFactORM,
    score: float,
    call_id: UUID,
    captured_at: datetime,
) -> Evidence:
    content = f"{fact.metric_key}={fact.value_num if fact.value_num is not None else fact.value_text}"
    if fact.unit:
        content = f"{content} {fact.unit}"
    return Evidence(
        evidence_id=uuid4(),
        source_type="graph_edge",
        title=f"Fact: {fact.metric_key}",
        content=content,
        citation_anchor=CitationAnchor(
            anchor_type="graph_ref",
            label="relation_fact",
            locator=f"ontology-relation-fact:{fact.id}",
        ),
        provenance=Provenance(
            workspace_id=fact.workspace_id,
            source_id=fact.id,
            tool_call_id=call_id,
            captured_at=captured_at,
        ),
        relation_ids=(fact.relation_id,),
        score=float(score),
    )


# Backward-compat names used by SearchToolConfigService
_keyword_score = keyword_score
_entity_to_evidence = entity_to_evidence
_relation_to_evidence = relation_to_evidence
_entity_fact_to_evidence = entity_fact_to_evidence
_relation_fact_to_evidence = relation_fact_to_evidence
