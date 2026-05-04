"""Fuse dense chunk retrieval with Graphiti graph search via Reciprocal Rank Fusion (RRF)."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from semantic_reasoning_agent.domain.contracts.evidence import Evidence
from semantic_reasoning_agent.infrastructure.graphiti.graphiti_evidence import graphiti_matches_to_evidence
from semantic_reasoning_agent.services.evidence_from_retrieval import retrieval_result_to_evidence
from semantic_reasoning_agent.services.retrieval_service import RetrievalService
from semantic_reasoning_agent.retrieval.ranking import RRF_K, reciprocal_rank_fuse

if TYPE_CHECKING:
    from semantic_reasoning_agent.infrastructure.graphiti.graphiti_gateway import GraphitiGateway


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
            group_ids=[workspace_id],
            limit=max(1, top_k),
            search_type="combined",
        )
        return graphiti_matches_to_evidence(
            matches,
            workspace_id=workspace_id,
            tool_call_id=tool_call_id,
        )

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


__all__ = ["HybridRetrievalService", "RRF_K", "reciprocal_rank_fuse"]
