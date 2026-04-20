from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status

from semantic_reasoning_agent.domain.contracts.tool_envelope import (
    OntologyContextRef,
    ToolConstraints,
    ToolEnvelope,
)
from semantic_reasoning_agent.entrypoints.dependencies import (
    get_tool_registry,
    get_tool_runtime,
)
from semantic_reasoning_agent.schemas.tools import (
    StandardToolInputSchema,
    StandardToolOutputSchema,
    ToolSpecSchema,
)
from semantic_reasoning_agent.services.tool_registry import ToolRegistry
from semantic_reasoning_agent.services.tool_runtime import ToolRuntime

router = APIRouter()

ToolFamilyQuery = Literal[
    "document",
    "retrieval",
    "ontology",
    "graph",
    "web",
    "mcp",
    "artifact",
    "admin",
]
RiskLevelQuery = Literal["low", "medium", "high"]


@router.get("", response_model=list[ToolSpecSchema])
def list_tools(
    family: ToolFamilyQuery | None = Query(default=None),
    max_risk: RiskLevelQuery | None = Query(default=None),
    registry: ToolRegistry = Depends(get_tool_registry),
) -> list[ToolSpecSchema]:
    specs = registry.list(family=family, max_risk=max_risk)
    return [_spec_to_schema(spec) for spec in specs]


@router.post("/{tool_name}/invoke", response_model=StandardToolOutputSchema)
def invoke_tool(
    tool_name: str,
    payload: StandardToolInputSchema,
    registry: ToolRegistry = Depends(get_tool_registry),
    runtime: ToolRuntime = Depends(get_tool_runtime),
) -> StandardToolOutputSchema:
    if payload.tool_name != tool_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Path tool '{tool_name}' does not match body tool_name "
                f"'{payload.tool_name}'."
            ),
        )
    if registry.spec(tool_name) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tool '{tool_name}' is not registered.",
        )

    envelope = _payload_to_envelope(payload)
    result = runtime.invoke(envelope)
    return _result_to_schema(result)


def _spec_to_schema(spec) -> ToolSpecSchema:  # noqa: ANN001
    return ToolSpecSchema(
        tool_name=spec.tool_name,
        tool_family=spec.tool_family,
        tool_type=spec.tool_type,
        version=spec.version,
        description=spec.description,
        input_schema=dict(spec.input_schema),
        input_schema_ref=spec.input_schema_ref,
        output_schema_ref=spec.output_schema_ref,
        capabilities=list(spec.capabilities),
        risk_level=spec.risk_level,
        side_effect_level=spec.side_effect_level,
        supports_parallel=spec.supports_parallel,
        supports_streaming=spec.supports_streaming,
        requires_confirmation=spec.requires_confirmation,
        timeout_ms=spec.timeout_ms,
        workspace_scope=spec.workspace_scope,
    )


def _payload_to_envelope(payload: StandardToolInputSchema) -> ToolEnvelope:
    ontology_ref = OntologyContextRef(
        domain=payload.ontology_context.domain,
        entity_hints=tuple(payload.ontology_context.entity_hints),
        relation_hints=tuple(payload.ontology_context.relation_hints),
        normalization_rules=tuple(payload.ontology_context.normalization_rules),
    )
    constraints = ToolConstraints(
        web_enabled=payload.constraints.web_enabled,
        freshness_required=payload.constraints.freshness_required,
        max_results=payload.constraints.max_results,
        timeout_ms=payload.constraints.timeout_ms,
    )
    return ToolEnvelope(
        call_id=payload.call_id,
        tool_name=payload.tool_name,
        workspace_id=payload.workspace_id,
        task_id=payload.task_id,
        task_type=payload.task_type,
        task_payload=dict(payload.task_payload),
        ontology_context=ontology_ref,
        arguments=dict(payload.arguments),
        constraints=constraints,
        workflow_id=payload.workflow_id,
    )


def _result_to_schema(result) -> StandardToolOutputSchema:  # noqa: ANN001
    from semantic_reasoning_agent.schemas.tools import (
        CitationAnchorSchema,
        EvidenceSchema,
        ProvenanceSchema,
        ToolMetaSchema,
    )

    evidence_schemas = [
        EvidenceSchema(
            evidence_id=e.evidence_id,
            source_type=e.source_type,
            title=e.title,
            content=e.content,
            citation_anchor=CitationAnchorSchema(
                anchor_type=e.citation_anchor.anchor_type,
                label=e.citation_anchor.label,
                locator=e.citation_anchor.locator,
            ),
            provenance=ProvenanceSchema(
                workspace_id=e.provenance.workspace_id,
                captured_at=e.provenance.captured_at,
                source_id=e.provenance.source_id,
                tool_call_id=e.provenance.tool_call_id,
                parser_version=e.provenance.parser_version,
                extractor_version=e.provenance.extractor_version,
                model=e.provenance.model,
            ),
            summary=e.summary,
            uri=e.uri,
            document_id=e.document_id,
            chunk_id=e.chunk_id,
            page=e.page,
            section=e.section,
            sheet_name=e.sheet_name,
            row_range=e.row_range,
            entity_ids=list(e.entity_ids),
            relation_ids=list(e.relation_ids),
            score=e.score,
            trust_score=e.trust_score,
            freshness_ts=e.freshness_ts,
        )
        for e in result.evidence
    ]
    return StandardToolOutputSchema(
        call_id=result.call_id,
        tool_name=result.tool_name,
        status=result.status,
        started_at=result.started_at,
        finished_at=result.finished_at,
        latency_ms=result.latency_ms,
        evidence=evidence_schemas,
        artifacts=[dict(a) for a in result.artifacts],
        state_patch=dict(result.state_patch),
        next_action_hints=list(result.next_action_hints),
        error_code=result.error_code,
        error_message=result.error_message,
        meta=ToolMetaSchema(
            provider=result.meta.provider,
            provider_version=result.meta.provider_version,
            trace_id=result.meta.trace_id,
        ),
    )
