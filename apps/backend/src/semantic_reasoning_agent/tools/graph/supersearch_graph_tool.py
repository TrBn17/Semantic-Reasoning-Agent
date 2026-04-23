"""`supersearch.graph` tool — runs a saved graph search config."""

from __future__ import annotations

from typing import Any

from semantic_reasoning_agent.core.runtime_constants import GRAPH_TOOL_TIMEOUT_MS
from semantic_reasoning_agent.core.time import utc_now
from semantic_reasoning_agent.domain.contracts.tool_envelope import (
    ToolEnvelope,
    ToolMeta,
    ToolResult,
)
from semantic_reasoning_agent.domain.contracts.tool_spec import ToolSpec
from semantic_reasoning_agent.schemas.search_tools import SearchToolRunRequest
from semantic_reasoning_agent.services.search_tool_service import (
    TOOL_NAME_GRAPH,
    SearchToolConfigNotFoundError,
    SearchToolConfigService,
)
from semantic_reasoning_agent.tools.base import Tool
from semantic_reasoning_agent.tools.retrieval.supersearch_docs_tool import _schema_to_evidence


_SPEC_INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "config_ref": {
            "type": "string",
            "description": "Identifier of the saved supersearch.graph configuration to execute.",
        },
        "query": {
            "type": "string",
            "description": "Natural-language question or search phrase for graph lookup.",
        },
        "top_k": {
            "type": "integer",
            "minimum": 1,
            "maximum": 50,
            "description": "Override for the configured default_top_k.",
        },
        "reranker": {
            "type": "string",
            "enum": ["cross_encoder", "rrf", "none"],
            "description": "Override for the configured reranker preset.",
        },
    },
    "required": ["config_ref", "query"],
    "additionalProperties": False,
}


class SuperSearchGraphTool(Tool):
    """Executes a persisted graph search configuration.

    Uses Graphiti when the runtime is enabled; otherwise falls back to
    a SQL-level lookup against the published ontology version for the
    configured workspace.
    """

    tool_name = TOOL_NAME_GRAPH

    SPEC = ToolSpec(
        tool_name=TOOL_NAME_GRAPH,
        tool_family="graph",
        tool_type="internal_service",
        version="1.0.0",
        description=(
            "Run a saved supersearch.graph configuration — ontology-scoped graph "
            "search with a configurable reranker, falls back to SQL ontology lookup "
            "when Graphiti is not available."
        ),
        input_schema=_SPEC_INPUT_SCHEMA,
        input_schema_ref="srag:supersearch.graph.in.v1",
        capabilities=("graph_search", "ontology_scope"),
        risk_level="low",
        side_effect_level="read_only",
        supports_parallel=True,
        timeout_ms=GRAPH_TOOL_TIMEOUT_MS,
    )

    def __init__(self, service: SearchToolConfigService) -> None:
        self._service = service

    def run(self, envelope: ToolEnvelope) -> ToolResult:
        arguments = envelope.arguments if isinstance(envelope.arguments, dict) else {}
        config_ref = arguments.get("config_ref")
        query = arguments.get("query")
        if not isinstance(config_ref, str) or not config_ref.strip():
            raise ValueError("supersearch.graph requires a non-empty 'config_ref' argument.")
        if not isinstance(query, str) or not query.strip():
            raise ValueError("supersearch.graph requires a non-empty 'query' argument.")

        payload = SearchToolRunRequest(
            query=query,
            top_k=arguments.get("top_k") if isinstance(arguments.get("top_k"), int) else None,
            reranker=arguments.get("reranker")
            if arguments.get("reranker") in {"cross_encoder", "rrf", "none"}
            else None,
        )

        now = utc_now()
        try:
            response = self._service.run(
                config_ref,
                payload,
                workspace_id=envelope.workspace_id,
            )
        except SearchToolConfigNotFoundError as exc:
            return ToolResult(
                call_id=envelope.call_id,
                tool_name=self.tool_name,
                status="failed",
                started_at=now,
                finished_at=now,
                latency_ms=0,
                error_code="config_not_found",
                error_message=str(exc),
                meta=ToolMeta(trace_id=str(envelope.call_id)),
            )

        evidence = tuple(_schema_to_evidence(item) for item in response.evidence)
        return ToolResult(
            call_id=envelope.call_id,
            tool_name=self.tool_name,
            status=response.status,
            started_at=now,
            finished_at=now,
            latency_ms=response.latency_ms,
            evidence=evidence,
            next_action_hints=tuple(response.next_action_hints),
            error_code=response.error_code,
            error_message=response.error_message,
            meta=ToolMeta(
                provider=response.meta.provider,
                provider_version=response.meta.provider_version,
                trace_id=response.meta.trace_id,
            ),
        )
