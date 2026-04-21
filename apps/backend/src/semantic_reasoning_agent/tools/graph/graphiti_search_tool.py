from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from semantic_reasoning_agent.domain.contracts.tool_envelope import ToolEnvelope, ToolMeta, ToolResult
from semantic_reasoning_agent.domain.contracts.tool_spec import ToolSpec
from semantic_reasoning_agent.infrastructure.graphiti.graphiti_gateway import GraphitiGateway
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
    },
    "required": ["query"],
    "additionalProperties": False,
}


class GraphitiSearchTool(Tool):
    tool_name = "graphiti.search"

    SPEC = ToolSpec(
        tool_name="graphiti.search",
        tool_family="graph",
        tool_type="internal_service",
        version="1.0.0",
        description="Searches the Graphiti runtime graph and returns matching graph edges and nodes as Evidence.",
        input_schema=_SPEC_INPUT_SCHEMA,
        input_schema_ref="srag:graphiti.search.in.v1",
        capabilities=("graph_search", "temporal_context"),
        risk_level="low",
        side_effect_level="read_only",
        supports_parallel=True,
        timeout_ms=10000,
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

        now = datetime.now(timezone.utc)
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

        matches = self._gateway.search(query=query, workspace_id=envelope.workspace_id, limit=max_results)
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
