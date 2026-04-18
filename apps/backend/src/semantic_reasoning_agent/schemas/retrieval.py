from pydantic import BaseModel, Field


class Citation(BaseModel):
    chunk_id: str
    document_id: str
    document_title: str
    document_type: str
    excerpt: str
    location_label: str
    source_url: str
    page_number: int | None = None
    heading_path: str | None = None
    sheet_name: str | None = None
    row_start: int | None = None
    row_end: int | None = None


class RetrievalResult(BaseModel):
    chunk_id: str
    document_id: str
    document_title: str
    document_type: str
    score: float
    excerpt: str
    citation: Citation


class RetrievalSearchRequest(BaseModel):
    query: str
    workspace_id: str | None = None
    document_ids: list[str] = Field(default_factory=list)
    top_k: int = 3


class RetrievalSearchResponse(BaseModel):
    query: str
    results: list[RetrievalResult]


class RetrievalReindexRequest(BaseModel):
    document_ids: list[str] = Field(default_factory=list)


class RetrievalReindexResponse(BaseModel):
    reindexed_document_ids: list[str]
