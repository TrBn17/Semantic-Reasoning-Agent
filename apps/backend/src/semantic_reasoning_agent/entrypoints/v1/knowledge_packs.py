from fastapi import APIRouter, Depends, HTTPException, Query, status

from semantic_reasoning_agent.entrypoints.dependencies import get_knowledge_pack_service
from semantic_reasoning_agent.schemas.knowledge_packs import (
    KnowledgePackAddDocumentRequest,
    KnowledgePackCreateRequest,
    KnowledgePackDocumentSummaryResponse,
    KnowledgePackResponse,
    KnowledgePackUpdateRequest,
)
from semantic_reasoning_agent.services.knowledge_pack_service import (
    KnowledgePackNotFoundError,
    KnowledgePackService,
    KnowledgePackValidationError,
)


router = APIRouter()


@router.get("", response_model=list[KnowledgePackResponse])
def list_knowledge_packs(
    workspace_id: str | None = Query(default=None),
    knowledge_pack_service: KnowledgePackService = Depends(get_knowledge_pack_service),
) -> list[KnowledgePackResponse]:
    return knowledge_pack_service.list_packs(workspace_id)


@router.post("", response_model=KnowledgePackResponse, status_code=status.HTTP_201_CREATED)
def create_knowledge_pack(
    payload: KnowledgePackCreateRequest,
    knowledge_pack_service: KnowledgePackService = Depends(get_knowledge_pack_service),
) -> KnowledgePackResponse:
    try:
        return knowledge_pack_service.create_pack(payload)
    except KnowledgePackValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/{pack_id}", response_model=KnowledgePackResponse)
def get_knowledge_pack(
    pack_id: str,
    knowledge_pack_service: KnowledgePackService = Depends(get_knowledge_pack_service),
) -> KnowledgePackResponse:
    try:
        return knowledge_pack_service.get_pack(pack_id)
    except KnowledgePackNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.patch("/{pack_id}", response_model=KnowledgePackResponse)
def update_knowledge_pack(
    pack_id: str,
    payload: KnowledgePackUpdateRequest,
    knowledge_pack_service: KnowledgePackService = Depends(get_knowledge_pack_service),
) -> KnowledgePackResponse:
    try:
        return knowledge_pack_service.update_pack(pack_id, payload)
    except KnowledgePackNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except KnowledgePackValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.delete("/{pack_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_knowledge_pack(
    pack_id: str,
    knowledge_pack_service: KnowledgePackService = Depends(get_knowledge_pack_service),
) -> None:
    try:
        knowledge_pack_service.delete_pack(pack_id)
    except KnowledgePackNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/{pack_id}/documents", response_model=list[KnowledgePackDocumentSummaryResponse])
def list_knowledge_pack_documents(
    pack_id: str,
    knowledge_pack_service: KnowledgePackService = Depends(get_knowledge_pack_service),
) -> list[KnowledgePackDocumentSummaryResponse]:
    try:
        return knowledge_pack_service.list_pack_documents(pack_id)
    except KnowledgePackNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post(
    "/{pack_id}/documents",
    response_model=list[KnowledgePackDocumentSummaryResponse],
    status_code=status.HTTP_201_CREATED,
)
def add_knowledge_pack_document(
    pack_id: str,
    payload: KnowledgePackAddDocumentRequest,
    knowledge_pack_service: KnowledgePackService = Depends(get_knowledge_pack_service),
) -> list[KnowledgePackDocumentSummaryResponse]:
    try:
        return knowledge_pack_service.add_document(pack_id, payload)
    except KnowledgePackNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except KnowledgePackValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.delete("/{pack_id}/documents/{document_id}", response_model=list[KnowledgePackDocumentSummaryResponse])
def remove_knowledge_pack_document(
    pack_id: str,
    document_id: str,
    knowledge_pack_service: KnowledgePackService = Depends(get_knowledge_pack_service),
) -> list[KnowledgePackDocumentSummaryResponse]:
    try:
        return knowledge_pack_service.remove_document(pack_id, document_id)
    except KnowledgePackNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
