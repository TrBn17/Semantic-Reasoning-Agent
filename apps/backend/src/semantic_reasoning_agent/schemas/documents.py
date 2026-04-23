from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class DocumentStatus(str, Enum):
    uploaded = "uploaded"
    parsed = "parsed"
    indexed = "indexed"
    failed = "failed"


class JobStatus(str, Enum):
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"


class DocumentResponse(BaseModel):
    id: str
    title: str
    filename: str
    workspace_id: str
    document_type: str
    status: DocumentStatus
    parser_version: str
    chunk_count: int = 0
    tags: list[str] = Field(default_factory=list)
    ingestion_options: dict[str, object] = Field(default_factory=dict)
    ingestion_mode: str = "both"
    source_url: str
    source_object_key: str | None = None
    source_content_type: str | None = None
    size_bytes: int | None = None
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    error_message: str | None = None


class DocumentIngestionOptionsResponse(BaseModel):
    ingestion_mode: str = "both"


class DocumentOptionChoice(BaseModel):
    value: str
    label: str
    description: str | None = None


class DocumentIngestionCapabilitiesResponse(BaseModel):
    supported_types: list[str]
    default_options: DocumentIngestionOptionsResponse
    ingestion_mode_options: list[DocumentOptionChoice]


class DocumentJobResponse(BaseModel):
    id: str
    name: str
    status: JobStatus = JobStatus.pending
    started_at: datetime | None = None
    finished_at: datetime | None = None
    error_message: str | None = None


class DocumentReprocessResponse(BaseModel):
    document: DocumentResponse
    jobs: list[DocumentJobResponse]


class DocumentArtifactResponse(BaseModel):
    id: str
    document_id: str
    workspace_id: str
    artifact_type: str
    name: str
    object_key: str
    public_url: str
    content_type: str
    size_bytes: int
    metadata: dict[str, object] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)


class DocumentExtractRequest(BaseModel):
    extraction_schema: dict[str, object] = Field(alias="schema_json")
    use_llm: bool = False
    force_ocr: bool = False
    strip_existing_ocr: bool = False


class DocumentExtractionRunResponse(BaseModel):
    id: str
    document_id: str
    workspace_id: str
    status: str
    extraction_schema: dict[str, object] = Field(alias="schema_json")
    result_json: dict[str, object] | None = None
    parser_version: str | None = None
    use_llm: bool = False
    error_message: str | None = None
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
