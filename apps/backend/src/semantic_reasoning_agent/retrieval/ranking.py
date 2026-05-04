"""Reciprocal Rank Fusion over ranked lists of Evidence (shared by hybrid + supersearch docs)."""

from __future__ import annotations

from dataclasses import replace

from semantic_reasoning_agent.domain.contracts.evidence import Evidence

RRF_K = 60


def _evidence_fuse_key(evidence: Evidence) -> str:
    if evidence.document_id and evidence.chunk_id:
        return f"chunk:{evidence.document_id}:{evidence.chunk_id}"
    if evidence.source_type in ("graph_node", "graph_edge") and evidence.provenance.source_id:
        return f"graph:{evidence.provenance.source_id}"
    return f"id:{evidence.evidence_id}"


def reciprocal_rank_fuse(
    ranked_lists: list[list[Evidence]],
    *,
    top_k: int,
    k: int = RRF_K,
) -> list[Evidence]:
    scores: dict[str, float] = {}
    best: dict[str, Evidence] = {}
    for items in ranked_lists:
        for rank, ev in enumerate(items, start=1):
            key = _evidence_fuse_key(ev)
            scores[key] = scores.get(key, 0.0) + 1.0 / (k + rank)
            best.setdefault(key, ev)
    ordered = sorted(scores.keys(), key=lambda key: scores[key], reverse=True)
    out: list[Evidence] = []
    for key in ordered[:top_k]:
        base = best[key]
        out.append(replace(base, score=scores[key]))
    return out
