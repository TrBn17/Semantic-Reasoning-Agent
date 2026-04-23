"""`supersearch.docs` tool — runs a saved docs search config."""

from __future__ import annotations

from typing import Any

from semantic_reasoning_agent.core.runtime_constants import DEFAULT_TOOL_TIMEOUT_MS
from semantic_reasoning_agent.core.time import utc_now
from semantic_reasoning_agent.domain.contracts.evidence import (
    CitationAnchor,
    Evidence,
    Provenance,
)
from semantic_reasoning_agent.domain.contracts.tool_envelope import (
    ToolEnvelope,
    ToolMeta,
    ToolResult,
)
from semantic_reasoning_agent.domain.contracts.tool_spec import ToolSpec
from semantic_reasoning_agent.schemas.search_tools import SearchToolRunRequest
from semantic_reasoning_agent.services.search_tool_service import (
    TOOL_NAME_DOCS,
    SearchToolConfigNotFoundError,
    SearchToolConfigService,
)
from semantic_reasoning_agent.tools.base import Tool


_SPEC_INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "config_ref": {
            "type": "string",
            "description": "Identifier of the saved supersearch.docs configuration to execute.",
        },
        "query": {
            "type": "string",
            "description": "Natural-language question or search phrase.",
        },
        "top_k": {
            "type": "integer",
            "minimum": 1,
            "maximum": 50,
            "description": "Override for the configured default_top_k.",
        },
        "bm25_enabled": {
            "type": "boolean",
            "description": "Runtime toggle for BM25 (overrides the saved config value).",
        },
        "fusion_strategy": {
            "type": "string",
            "enum": ["semantic_only", "bm25_only", "hybrid_rrf"],
            "description": "Override for the configured fusion strategy.",
        },
        "document_ids": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Optional runtime document scope override.",
        },
    },
    "required": ["config_ref", "query"],
    "additionalProperties": False,
}


class SuperSearchDocsTool(Tool):
    """Executes a persisted docs search configuration.

    The tool looks up a ``SearchToolConfigORM`` row by ``config_ref``,
    resolves provider/model readiness, and runs the semantic + BM25
    fusion pipeline. Output is returned as standard ``Evidence`` rows.
    """

    tool_name = TOOL_NAME_DOCS

    SPEC = ToolSpec(
        tool_name=TOOL_NAME_DOCS,
        tool_family="retrieval",
        tool_type="internal_service",
        version="1.0.0",
        description=(
            "Run a saved supersearch.docs configuration — semantic retrieval with "
            "optional BM25 + RRF fusion, scoped to a workspace collection."
        ),
        input_schema=_SPEC_INPUT_SCHEMA,
        input_schema_ref="srag:supersearch.docs.in.v1",
        capabilities=("citation", "score", "bm25"),
        risk_level="low",
        side_effect_level="read_only",
        supports_parallel=True,
        timeout_ms=DEFAULT_TOOL_TIMEOUT_MS,
    )

    def __init__(self, service: SearchToolConfigService) -> None:
        self._service = service

    def run(self, envelope: ToolEnvelope) -> ToolResult:
        arguments = envelope.arguments if isinstance(envelope.arguments, dict) else {}
        config_ref = arguments.get("config_ref")
        query = arguments.get("query")
        if not isinstance(config_ref, str) or not config_ref.strip():
            raise ValueError("supersearch.docs requires a non-empty 'config_ref' argument.")
        if not isinstance(query, str) or not query.strip():
            raise ValueError("supersearch.docs requires a non-empty 'query' argument.")

        payload = SearchToolRunRequest(
            query=query,
            top_k=arguments.get("top_k") if isinstance(arguments.get("top_k"), int) else None,
            bm25_enabled=arguments.get("bm25_enabled")
            if isinstance(arguments.get("bm25_enabled"), bool)
            else None,
            fusion_strategy=arguments.get("fusion_strategy")
            if arguments.get("fusion_strategy") in {"semantic_only", "bm25_only", "hybrid_rrf"}
            else None,
            document_ids=[
                str(item)
                for item in arguments.get("document_ids", [])
                if isinstance(item, str) and item.strip()
            ]
            or None,
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

        evidence: list[Evidence] = []
        for item in response.evidence:
            evidence.append(_schema_to_evidence(item))

        return ToolResult(
            call_id=envelope.call_id,
            tool_name=self.tool_name,
            status=response.status,
            started_at=now,
            finished_at=now,
            latency_ms=response.latency_ms,
            evidence=tuple(evidence),
            next_action_hints=tuple(response.next_action_hints),
            error_code=response.error_code,
            error_message=response.error_message,
            meta=ToolMeta(
                provider=response.meta.provider,
                provider_version=response.meta.provider_version,
                trace_id=response.meta.trace_id,
            ),
        )


def _schema_to_evidence(schema) -> Evidence:  # noqa: ANN001
    return Evidence(
        evidence_id=schema.evidence_id,
        source_type=schema.source_type,
        title=schema.title,
        content=schema.content,
        citation_anchor=CitationAnchor(
            anchor_type=schema.citation_anchor.anchor_type,
            label=schema.citation_anchor.label,
            locator=schema.citation_anchor.locator,
        ),
        provenance=Provenance(
            workspace_id=schema.provenance.workspace_id,
            captured_at=schema.provenance.captured_at,
            source_id=schema.provenance.source_id,
            tool_call_id=schema.provenance.tool_call_id,
            parser_version=schema.provenance.parser_version,
            extractor_version=schema.provenance.extractor_version,
            model=schema.provenance.model,
        ),
        summary=schema.summary,
        uri=schema.uri,
        document_id=schema.document_id,
        chunk_id=schema.chunk_id,
        page=schema.page,
        section=schema.section,
        sheet_name=schema.sheet_name,
        row_range=schema.row_range,
        entity_ids=tuple(schema.entity_ids),
        relation_ids=tuple(schema.relation_ids),
        score=schema.score,
        trust_score=schema.trust_score,
        freshness_ts=schema.freshness_ts,
    )
