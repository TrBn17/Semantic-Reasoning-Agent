from __future__ import annotations


def clamp_confidence(value: float) -> float:
    return max(0.0, min(1.0, value))


def combine_confidence(
    *,
    rule_score: float,
    llm_score: float | None,
    evidence_count: int,
    ontology_match_score: float,
) -> float:
    llm_component = llm_score if llm_score is not None else rule_score
    evidence_bonus = min(0.12, 0.02 * max(0, evidence_count - 1))
    aggregate = (rule_score * 0.45) + (llm_component * 0.4) + (ontology_match_score * 0.15) + evidence_bonus
    return clamp_confidence(aggregate)
