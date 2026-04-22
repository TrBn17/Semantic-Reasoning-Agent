from __future__ import annotations

from typing import TYPE_CHECKING, Any

from semantic_reasoning_agent.domain.contracts.evidence import Evidence
from semantic_reasoning_agent.domain.contracts.tool_envelope import (
    ToolEnvelope,
    ToolMeta,
    ToolResult,
)
from semantic_reasoning_agent.domain.contracts.tool_spec import ToolSpec
from semantic_reasoning_agent.core.runtime_constants import DEFAULT_TASK_TOP_K, DEFAULT_TOOL_TIMEOUT_MS, TOOL_RETRIEVAL_INTERNAL
from semantic_reasoning_agent.core.time import utc_now
from semantic_reasoning_agent.services.evidence_from_retrieval import retrieval_result_to_evidence
from semantic_reasoning_agent.services.hybrid_retrieval_service import HybridRetrievalService
from semantic_reasoning_agent.services.retrieval_service import RetrievalService
from semantic_reasoning_agent.tools.base import Tool

if TYPE_CHECKING:
    from semantic_reasoning_agent.infrastructure.graphiti.graphiti_gateway import GraphitiGateway


_SPEC_INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "query": {
            "type": "string",
            "description": "Natural-language question or search phrase.",
        },
        "document_ids": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Optional subset of workspace document IDs to search within.",
        },
        "top_k": {
            "type": "integer",
            "minimum": 1,
            "maximum": 20,
            "default": DEFAULT_TASK_TOP_K,
            "description": "Number of evidence items to return after ranking.",
        },
        "mode": {
            "type": "string",
            "enum": ["hybrid", "chunks", "graph"],
            "default": "hybrid",
            "description": (
                "hybrid: fuse workspace chunks with Graphiti graph matches (RRF) when Graphiti is enabled; "
                "chunks: dense chunk retrieval only; graph: Graphiti graph search only."
            ),
        },
    },
    "required": ["query"],
    "additionalProperties": False,
}


class InternalRetrievalTool(Tool):
    """Wraps ``RetrievalService.search`` as a §9 Tool.

    Returns one ``Evidence`` per ranked chunk, each carrying its citation
    anchor (page / section / sheet range) and full provenance pointing back
    to the document + tool call. Optional ``hybrid`` mode merges Graphiti
    graph hits with chunk retrieval via reciprocal-rank fusion.
    """

    tool_name = TOOL_RETRIEVAL_INTERNAL

    SPEC = ToolSpec(
        tool_name=TOOL_RETRIEVAL_INTERNAL,
        tool_family="retrieval",
        tool_type="internal_service",
        version="1.1.0",
        description=(
            "Internal RAG over workspace-indexed document chunks, optionally fused "
            "with Graphiti graph search (hybrid mode). Returns ranked Evidence with "
            "citation anchors."
        ),
        input_schema=_SPEC_INPUT_SCHEMA,
        input_schema_ref="srag:retrieval.internal.in.v1",
        capabilities=("citation", "score"),
        risk_level="low",
        side_effect_level="read_only",
        supports_parallel=True,
        timeout_ms=DEFAULT_TOOL_TIMEOUT_MS,
    )

    def __init__(
        self,
        retrieval_service: RetrievalService,
        graphiti_gateway: GraphitiGateway | None = None,
    ) -> None:
        self._retrieval_service = retrieval_service
        self._hybrid = HybridRetrievalService(retrieval_service, graphiti_gateway)

    def run(self, envelope: ToolEnvelope) -> ToolResult:
        arguments = envelope.arguments
        query = arguments.get("query") if isinstance(arguments, dict) else None
        if not isinstance(query, str) or not query.strip():
            raise ValueError("retrieval.internal requires a non-empty 'query' argument.")

        document_ids_raw = arguments.get("document_ids") if isinstance(arguments, dict) else None
        document_ids: list[str] | None = None
        if isinstance(document_ids_raw, list):
            document_ids = [str(item) for item in document_ids_raw if item]

        top_k = arguments.get("top_k") if isinstance(arguments, dict) else None
        if not isinstance(top_k, int) or top_k <= 0:
            top_k = min(envelope.constraints.max_results or DEFAULT_TASK_TOP_K, 10)

        mode_raw = arguments.get("mode") if isinstance(arguments, dict) else None
        mode = mode_raw if isinstance(mode_raw, str) and mode_raw in {"hybrid", "chunks", "graph"} else "hybrid"

        now = utc_now()
        evidence_list: list[Evidence]

        if mode == "graph":
            evidence_list = self._hybrid.search_graph_evidence(
                query=query,
                workspace_id=envelope.workspace_id,
                tool_call_id=envelope.call_id,
                top_k=top_k,
            )
        elif mode == "hybrid" and self._hybrid.graphiti_ready():
            evidence_list = self._hybrid.search_hybrid(
                query=query,
                workspace_id=envelope.workspace_id,
                document_ids=document_ids,
                top_k=top_k,
                tool_call_id=envelope.call_id,
                captured_at=now,
            )
        else:
            search_response = self._retrieval_service.search(
                query=query,
                workspace_id=envelope.workspace_id,
                document_ids=document_ids,
                top_k=top_k,
            )
            evidence_list = [
                retrieval_result_to_evidence(
                    result,
                    workspace_id=envelope.workspace_id,
                    tool_call_id=envelope.call_id,
                    captured_at=now,
                )
                for result in search_response.results
            ]

        evidence = tuple(evidence_list)
        return ToolResult(
            call_id=envelope.call_id,
            tool_name=self.tool_name,
            status="success" if evidence else "partial",
            started_at=now,
            finished_at=now,
            latency_ms=0,
            evidence=evidence,
            next_action_hints=(
                () if evidence else ("no_internal_match",)
            ),
            meta=ToolMeta(),
        )
