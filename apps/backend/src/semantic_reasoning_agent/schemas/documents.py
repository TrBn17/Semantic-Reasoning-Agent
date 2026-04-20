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
    source_url: str
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    error_message: str | None = None


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


class DocumentUploadFailure(BaseModel):
    filename: str
    reason: str


class DocumentBatchUploadResponse(BaseModel):
    uploaded: list[DocumentResponse] = Field(default_factory=list)
    failed: list[DocumentUploadFailure] = Field(default_factory=list)
