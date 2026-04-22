from fastapi import APIRouter, Depends, HTTPException, Query, status

from semantic_reasoning_agent.entrypoints.dependencies import get_knowledge_pack_service
from semantic_reasoning_agent.schemas.knowledge_packs import (
    KnowledgePackCreateRequest,
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
