from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from semantic_reasoning_agent.core.runtime_constants import DEFAULT_TOOL_TIMEOUT_MS
ToolFamilySchema = Literal[
    "document",
    "retrieval",
    "ontology",
    "graph",
    "web",
    "mcp",
    "artifact",
    "admin",
]
ToolTypeSchema = Literal["internal_service", "external_adapter", "worker_job"]
RiskLevelSchema = Literal["low", "medium", "high"]
SideEffectLevelSchema = Literal["read_only", "write_internal", "write_external"]
WorkspaceScopeSchema = Literal["workspace", "global"]
ToolStatusSchema = Literal["success", "partial", "failed"]
SourceTypeSchema = Literal[
    "internal_chunk",
    "web_page",
    "graph_node",
    "graph_edge",
    "mcp_result",
    "generated_artifact",
]
AnchorTypeSchema = Literal[
    "page",
    "section",
    "sheet_row",
    "url_fragment",
    "graph_ref",
    "artifact_ref",
]


class ToolSpecSchema(BaseModel):
    """API mirror of ``domain.contracts.tool_spec.ToolSpec``."""

    model_config = ConfigDict(frozen=True)

    tool_name: str
    tool_family: ToolFamilySchema
    tool_type: ToolTypeSchema
    version: str
    description: str
    input_schema: dict[str, Any]
    input_schema_ref: str = ""
    output_schema_ref: str = "srag:tool.out.v1"
    capabilities: list[str] = Field(default_factory=list)
    risk_level: RiskLevelSchema = "low"
    side_effect_level: SideEffectLevelSchema = "read_only"
    supports_parallel: bool = True
    supports_streaming: bool = False
    requires_confirmation: bool = False
    timeout_ms: int = DEFAULT_TOOL_TIMEOUT_MS
    workspace_scope: WorkspaceScopeSchema = "workspace"


class OntologyContextRefSchema(BaseModel):
    model_config = ConfigDict(frozen=True)

    domain: str | None = None
    entity_hints: list[str] = Field(default_factory=list)
    relation_hints: list[str] = Field(default_factory=list)
    normalization_rules: list[dict[str, Any]] = Field(default_factory=list)


class ToolConstraintsSchema(BaseModel):
    model_config = ConfigDict(frozen=True)

    web_enabled: bool = False
    freshness_required: bool = False
    max_results: int = 10
    timeout_ms: int = DEFAULT_TOOL_TIMEOUT_MS


class StandardToolInputSchema(BaseModel):
    """Standard Tool Input — AGENTS.md §9. The body of POST /tools/{name}/invoke."""

    model_config = ConfigDict(frozen=True)

    call_id: UUID
    tool_name: str
    workspace_id: str
    task_id: str
    task_type: str
    task_payload: dict[str, Any] = Field(default_factory=dict)
    ontology_context: OntologyContextRefSchema = Field(default_factory=OntologyContextRefSchema)
    arguments: dict[str, Any] = Field(default_factory=dict)
    constraints: ToolConstraintsSchema = Field(default_factory=ToolConstraintsSchema)
    workflow_id: str | None = None


class CitationAnchorSchema(BaseModel):
    model_config = ConfigDict(frozen=True)

    anchor_type: AnchorTypeSchema
    label: str
    locator: str


class ProvenanceSchema(BaseModel):
    model_config = ConfigDict(frozen=True)

    workspace_id: str
    captured_at: datetime
    source_id: str | None = None
    tool_call_id: UUID | None = None
    parser_version: str | None = None
    extractor_version: str | None = None
    model: str | None = None


class EvidenceSchema(BaseModel):
    model_config = ConfigDict(frozen=True)

    evidence_id: UUID
    source_type: SourceTypeSchema
    title: str
    content: str
    citation_anchor: CitationAnchorSchema
    provenance: ProvenanceSchema
    summary: str | None = None
    uri: str | None = None
    document_id: str | None = None
    chunk_id: str | None = None
    page: int | None = None
    section: str | None = None
    sheet_name: str | None = None
    row_range: str | None = None
    entity_ids: list[str] = Field(default_factory=list)
    relation_ids: list[str] = Field(default_factory=list)
    score: float = 0.0
    trust_score: float = 0.0
    freshness_ts: datetime | None = None


class ToolMetaSchema(BaseModel):
    model_config = ConfigDict(frozen=True)

    provider: str | None = None
    provider_version: str | None = None
    trace_id: str | None = None


class StandardToolOutputSchema(BaseModel):
    """Standard Tool Output — AGENTS.md §9. Response body of POST /tools/{name}/invoke."""

    model_config = ConfigDict(frozen=True)

    call_id: UUID
    tool_name: str
    status: ToolStatusSchema
    started_at: datetime
    finished_at: datetime
    latency_ms: int
    evidence: list[EvidenceSchema] = Field(default_factory=list)
    artifacts: list[dict[str, Any]] = Field(default_factory=list)
    state_patch: dict[str, Any] = Field(default_factory=dict)
    next_action_hints: list[str] = Field(default_factory=list)
    error_code: str | None = None
    error_message: str | None = None
    meta: ToolMetaSchema = Field(default_factory=ToolMetaSchema)
