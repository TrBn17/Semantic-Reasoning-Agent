from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class OntologyBuildStatus(str, Enum):
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"
    published = "published"


class OntologyReviewStatus(str, Enum):
    pending_review = "pending_review"
    approved = "approved"
    rejected = "rejected"


class OntologyStepStatus(str, Enum):
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"


class OntologyReviewAction(str, Enum):
    approve = "approve"
    reject = "reject"


class OntologyBuildCreateRequest(BaseModel):
    document_id: str
    workspace_id: str | None = None
    provider: str | None = None
    model: str | None = None


class OntologyBuildStepResponse(BaseModel):
    id: str
    name: str
    status: OntologyStepStatus
    detail: str | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None


class OntologyAttributeDefinitionResponse(BaseModel):
    name: str
    value_type: str = "text"
    description: str | None = None


class OntologySourceTargetDefinitionResponse(BaseModel):
    source_entity_type: str
    target_entity_type: str


class OntologyEntityTypeDefinitionResponse(BaseModel):
    id: str
    version_id: str | None = None
    workspace_id: str
    name: str
    description: str | None = None
    attributes: list[OntologyAttributeDefinitionResponse] = Field(default_factory=list)
    examples: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=utc_now)


class OntologyRelationTypeDefinitionResponse(BaseModel):
    id: str
    version_id: str | None = None
    workspace_id: str
    name: str
    description: str | None = None
    attributes: list[OntologyAttributeDefinitionResponse] = Field(default_factory=list)
    allowed_source_targets: list[OntologySourceTargetDefinitionResponse] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=utc_now)


class OntologyCandidateEntityResponse(BaseModel):
    id: str
    build_id: str
    document_id: str
    workspace_id: str
    name: str
    canonical_name: str
    resolution_key: str
    entity_type: str
    confidence: float
    status: OntologyReviewStatus
    source_chunk_id: str | None = None
    evidence_text: str
    provenance: dict[str, Any] = Field(default_factory=dict)
    aliases: list[str] = Field(default_factory=list)
    merged_into_entity_id: str | None = None
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class OntologyCandidateRelationResponse(BaseModel):
    id: str
    build_id: str
    document_id: str
    workspace_id: str
    source_entity_id: str | None = None
    target_entity_id: str | None = None
    source_name: str
    target_name: str
    relation_type: str
    confidence: float
    status: OntologyReviewStatus
    source_chunk_id: str | None = None
    evidence_text: str
    provenance: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class OntologyBuildResponse(BaseModel):
    id: str
    document_id: str
    workspace_id: str
    status: OntologyBuildStatus
    domain: str | None = None
    provider: str | None = None
    model: str | None = None
    created_at: datetime = Field(default_factory=utc_now)
    started_at: datetime | None = None
    finished_at: datetime | None = None
    updated_at: datetime = Field(default_factory=utc_now)
    error_message: str | None = None
    published_version_id: str | None = None
    entity_count: int = 0
    relation_count: int = 0
    pending_entity_count: int = 0
    pending_relation_count: int = 0
    entity_type_definitions: list[OntologyEntityTypeDefinitionResponse] = Field(default_factory=list)
    relation_type_definitions: list[OntologyRelationTypeDefinitionResponse] = Field(default_factory=list)
    steps: list[OntologyBuildStepResponse] = Field(default_factory=list)


class OntologyReviewRequest(BaseModel):
    action: OntologyReviewAction


class OntologyVersionResponse(BaseModel):
    id: str
    workspace_id: str
    version_number: int
    source_build_id: str
    created_at: datetime = Field(default_factory=utc_now)
    entity_type_count: int = 0
    relation_type_count: int = 0
    entity_count: int = 0
    relation_count: int = 0


class OntologyEntityResponse(BaseModel):
    id: str
    version_id: str
    workspace_id: str
    resolution_key: str
    name: str
    entity_type: str
    aliases: list[str] = Field(default_factory=list)
    source_build_id: str
    source_document_id: str
    created_at: datetime = Field(default_factory=utc_now)


class OntologyRelationResponse(BaseModel):
    id: str
    version_id: str
    workspace_id: str
    source_entity_id: str
    target_entity_id: str
    relation_type: str
    confidence: float
    source_build_id: str
    source_document_id: str
    evidence_text: str
    provenance: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)


class OntologyPublishResponse(BaseModel):
    build: OntologyBuildResponse
    version: OntologyVersionResponse


class OntologyGraphResponse(BaseModel):
    workspace_id: str
    version: OntologyVersionResponse | None = None
    entity_type_definitions: list[OntologyEntityTypeDefinitionResponse] = Field(default_factory=list)
    relation_type_definitions: list[OntologyRelationTypeDefinitionResponse] = Field(default_factory=list)
    entities: list[OntologyEntityResponse] = Field(default_factory=list)
    relations: list[OntologyRelationResponse] = Field(default_factory=list)
