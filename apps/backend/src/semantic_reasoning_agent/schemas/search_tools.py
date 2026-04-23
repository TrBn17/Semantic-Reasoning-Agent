from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from semantic_reasoning_agent.schemas.tools import EvidenceSchema, ToolMetaSchema

SearchToolType = Literal["docs", "graph"]
FusionStrategy = Literal["semantic_only", "bm25_only", "hybrid_rrf"]
CollectionTarget = Literal["workspace", "documents"]
OntologyScope = Literal["published", "version"]
GraphSearchType = Literal["nodes", "edges", "combined"]
GraphReranker = Literal["cross_encoder", "rrf", "none"]


class SearchToolConfigResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str
    workspace_id: str
    tool_type: SearchToolType
    name: str
    description: str = ""
    provider: str
    model: str
    default_top_k: int = 5

    collection_target: CollectionTarget = "workspace"
    document_ids: list[str] = Field(default_factory=list)
    bm25_enabled: bool = False
    fusion_strategy: FusionStrategy = "semantic_only"

    ontology_scope: OntologyScope = "published"
    ontology_version_id: str | None = None
    graph_search_type: GraphSearchType = "combined"
    reranker: GraphReranker = "rrf"

    config_metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime

    ready: bool = False
    ready_reason: str = ""


class SearchToolConfigCreateRequest(BaseModel):
    workspace_id: str | None = None
    tool_type: SearchToolType
    name: str = Field(..., min_length=1, max_length=128)
    description: str = ""
    provider: str
    model: str
    default_top_k: int = Field(default=5, ge=1, le=50)

    collection_target: CollectionTarget = "workspace"
    document_ids: list[str] = Field(default_factory=list)
    bm25_enabled: bool = False
    fusion_strategy: FusionStrategy = "semantic_only"

    ontology_scope: OntologyScope = "published"
    ontology_version_id: str | None = None
    graph_search_type: GraphSearchType = "combined"
    reranker: GraphReranker = "rrf"

    config_metadata: dict[str, Any] = Field(default_factory=dict)


class SearchToolConfigUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=128)
    description: str | None = None
    provider: str | None = None
    model: str | None = None
    default_top_k: int | None = Field(default=None, ge=1, le=50)

    collection_target: CollectionTarget | None = None
    document_ids: list[str] | None = None
    bm25_enabled: bool | None = None
    fusion_strategy: FusionStrategy | None = None

    ontology_scope: OntologyScope | None = None
    ontology_version_id: str | None = None
    graph_search_type: GraphSearchType | None = None
    reranker: GraphReranker | None = None

    config_metadata: dict[str, Any] | None = None


class SearchToolRunRequest(BaseModel):
    query: str = Field(..., min_length=1)
    top_k: int | None = Field(default=None, ge=1, le=50)
    bm25_enabled: bool | None = None
    fusion_strategy: FusionStrategy | None = None
    reranker: GraphReranker | None = None


class SearchToolRunResponse(BaseModel):
    config_id: str
    tool_type: SearchToolType
    tool_name: str
    status: Literal["success", "partial", "failed"]
    query: str
    evidence: list[EvidenceSchema] = Field(default_factory=list)
    next_action_hints: list[str] = Field(default_factory=list)
    error_code: str | None = None
    error_message: str | None = None
    latency_ms: int = 0
    meta: ToolMetaSchema = Field(default_factory=ToolMetaSchema)
