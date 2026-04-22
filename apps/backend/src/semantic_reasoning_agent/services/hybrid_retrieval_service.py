"""Fuse dense chunk retrieval with Graphiti graph search via Reciprocal Rank Fusion (RRF)."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from semantic_reasoning_agent.domain.contracts.evidence import Evidence
from semantic_reasoning_agent.infrastructure.graphiti.graphiti_mapper import map_edge_to_evidence, map_node_to_evidence
from semantic_reasoning_agent.services.evidence_from_retrieval import retrieval_result_to_evidence
from semantic_reasoning_agent.services.retrieval_service import RetrievalService

if TYPE_CHECKING:
    from semantic_reasoning_agent.infrastructure.graphiti.graphiti_gateway import GraphitiGateway

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


class HybridRetrievalService:
    def __init__(
        self,
        retrieval_service: RetrievalService,
        graphiti_gateway: GraphitiGateway | None,
    ) -> None:
        self._retrieval = retrieval_service
        self._gateway = graphiti_gateway

    def graphiti_ready(self) -> bool:
        return self._gateway is not None and self._gateway.is_enabled()

    def search_graph_evidence(
        self,
        *,
        query: str,
        workspace_id: str,
        tool_call_id: UUID,
        top_k: int,
    ) -> list[Evidence]:
        gw = self._gateway
        if gw is None or not gw.is_enabled():
            return []
        matches = gw.search(
            query=query,
            workspace_id=workspace_id,
            limit=max(1, top_k),
            search_type="combined",
        )
        evidence: list[Evidence] = []
        for match in matches:
            if match.kind == "edge":
                evidence.append(
                    map_edge_to_evidence(
                        match.item,
                        workspace_id=workspace_id,
                        tool_call_id=tool_call_id,
                        score=match.score,
                    )
                )
            else:
                evidence.append(
                    map_node_to_evidence(
                        match.item,
                        workspace_id=workspace_id,
                        tool_call_id=tool_call_id,
                        score=match.score,
                    )
                )
        return evidence

    def search_hybrid(
        self,
        *,
        query: str,
        workspace_id: str,
        document_ids: list[str] | None,
        top_k: int,
        tool_call_id: UUID,
        captured_at: datetime,
    ) -> list[Evidence]:
        chunk_cap = min(max(top_k, 1) * 2, 40)
        chunk_resp = self._retrieval.search(
            query=query,
            workspace_id=workspace_id,
            document_ids=document_ids,
            top_k=chunk_cap,
        )
        chunk_evidence = [
            retrieval_result_to_evidence(
                r,
                workspace_id=workspace_id,
                tool_call_id=tool_call_id,
                captured_at=captured_at,
            )
            for r in chunk_resp.results
        ]
        graph_evidence = self.search_graph_evidence(
            query=query,
            workspace_id=workspace_id,
            tool_call_id=tool_call_id,
            top_k=chunk_cap,
        )
        if not graph_evidence:
            return chunk_evidence[:top_k]
        if not chunk_evidence:
            return graph_evidence[:top_k]
        fused = reciprocal_rank_fuse([chunk_evidence, graph_evidence], top_k=top_k)
        return fused
