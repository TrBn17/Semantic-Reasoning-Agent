from __future__ import annotations

from typing import Any

from semantic_reasoning_agent.core.runtime_constants import GRAPH_TOOL_TIMEOUT_MS, TOOL_GRAPHITI_SEARCH
from semantic_reasoning_agent.core.time import utc_now
from semantic_reasoning_agent.domain.contracts.tool_envelope import ToolEnvelope, ToolMeta, ToolResult
from semantic_reasoning_agent.domain.contracts.tool_spec import ToolSpec
from semantic_reasoning_agent.infrastructure.graphiti.graphiti_gateway import (
    GraphitiGateway,
    RerankerMode,
    SearchType,
)
from semantic_reasoning_agent.infrastructure.graphiti.graphiti_mapper import map_edge_to_evidence, map_node_to_evidence
from semantic_reasoning_agent.tools.base import Tool


_SPEC_INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "query": {"type": "string", "description": "Natural-language graph query."},
        "max_results": {
            "type": "integer",
            "minimum": 1,
            "maximum": 20,
            "default": 5,
            "description": "Maximum graph matches to surface.",
        },
        "search_type": {
            "type": "string",
            "enum": ["nodes", "edges", "combined"],
            "default": "combined",
            "description": "Restrict Graphiti search to nodes, edges, or both.",
        },
        "center_node_uuid": {
            "type": "string",
            "description": "Optional center node UUID for reranked / neighborhood-aware search.",
        },
        "reranker": {
            "type": "string",
            "enum": ["cross_encoder", "rrf", "none"],
            "default": "cross_encoder",
            "description": "Reranker recipe; 'none' maps to RRF-only combined search.",
        },
    },
    "required": ["query"],
    "additionalProperties": False,
}


class GraphitiSearchTool(Tool):
    tool_name = TOOL_GRAPHITI_SEARCH

    SPEC = ToolSpec(
        tool_name=TOOL_GRAPHITI_SEARCH,
        tool_family="graph",
        tool_type="internal_service",
        version="1.1.0",
        description="Searches the Graphiti runtime graph and returns matching graph edges and nodes as Evidence.",
        input_schema=_SPEC_INPUT_SCHEMA,
        input_schema_ref="srag:graphiti.search.in.v1",
        capabilities=("graph_search", "temporal_context"),
        risk_level="low",
        side_effect_level="read_only",
        supports_parallel=True,
        timeout_ms=GRAPH_TOOL_TIMEOUT_MS,
    )

    def __init__(self, gateway: GraphitiGateway) -> None:
        self._gateway = gateway

    def run(self, envelope: ToolEnvelope) -> ToolResult:
        arguments = envelope.arguments if isinstance(envelope.arguments, dict) else {}
        query = arguments.get("query")
        if not isinstance(query, str) or not query.strip():
            raise ValueError("graphiti.search requires a non-empty 'query' argument.")
        max_results = arguments.get("max_results")
        if not isinstance(max_results, int) or max_results <= 0:
            max_results = envelope.constraints.max_results

        search_type = _coerce_search_type(arguments.get("search_type"))

        center_raw = arguments.get("center_node_uuid")
        center_node_uuid = center_raw if isinstance(center_raw, str) and center_raw.strip() else None

        reranker = _coerce_reranker(arguments.get("reranker"))

        now = utc_now()
        if not self._gateway.is_enabled():
            return ToolResult(
                call_id=envelope.call_id,
                tool_name=self.tool_name,
                status="partial",
                started_at=now,
                finished_at=now,
                latency_ms=0,
                next_action_hints=("graphiti_disabled",),
                meta=ToolMeta(provider="graphiti"),
            )

        matches = self._gateway.search(
            query=query,
            workspace_id=envelope.workspace_id,
            limit=max_results,
            search_type=search_type,
            center_node_uuid=center_node_uuid,
            valid_at=None,
            reranker=reranker,
        )
        evidence = []
        for match in matches:
            if match.kind == "edge":
                evidence.append(
                    map_edge_to_evidence(
                        match.item,
                        workspace_id=envelope.workspace_id,
                        tool_call_id=envelope.call_id,
                        score=match.score,
                    )
                )
            else:
                evidence.append(
                    map_node_to_evidence(
                        match.item,
                        workspace_id=envelope.workspace_id,
                        tool_call_id=envelope.call_id,
                        score=match.score,
                    )
                )
        return ToolResult(
            call_id=envelope.call_id,
            tool_name=self.tool_name,
            status="success" if evidence else "partial",
            started_at=now,
            finished_at=now,
            latency_ms=0,
            evidence=tuple(evidence),
            next_action_hints=(() if evidence else ("no_graph_match",)),
            meta=ToolMeta(provider="graphiti"),
        )


def _coerce_search_type(raw: object) -> SearchType:
    if raw == "nodes":
        return "nodes"
    if raw == "edges":
        return "edges"
    return "combined"


def _coerce_reranker(raw: object) -> RerankerMode:
    if raw == "rrf":
        return "rrf"
    if raw == "none":
        return "none"
    return "cross_encoder"
