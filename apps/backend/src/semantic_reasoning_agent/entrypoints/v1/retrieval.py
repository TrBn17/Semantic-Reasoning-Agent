from fastapi import APIRouter, Depends

from semantic_reasoning_agent.entrypoints.dependencies import get_document_service, get_retrieval_service
from semantic_reasoning_agent.schemas.retrieval import (
    RetrievalReindexRequest,
    RetrievalReindexResponse,
    RetrievalSearchRequest,
    RetrievalSearchResponse,
)
from semantic_reasoning_agent.services.document_service import DocumentService
from semantic_reasoning_agent.services.retrieval_service import RetrievalService


router = APIRouter()


@router.post("/search", response_model=RetrievalSearchResponse)
def search_documents(
    payload: RetrievalSearchRequest,
    retrieval_service: RetrievalService = Depends(get_retrieval_service),
) -> RetrievalSearchResponse:
    return retrieval_service.search(
        query=payload.query,
        workspace_id=payload.workspace_id,
        document_ids=payload.document_ids,
        top_k=payload.top_k,
    )


@router.post("/reindex", response_model=RetrievalReindexResponse)
def reindex_documents(
    payload: RetrievalReindexRequest,
    document_service: DocumentService = Depends(get_document_service),
) -> RetrievalReindexResponse:
    return RetrievalReindexResponse(
        reindexed_document_ids=document_service.reprocess_documents(payload.document_ids),
    )
