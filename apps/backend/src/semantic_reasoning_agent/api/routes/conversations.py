from fastapi import APIRouter, Depends, HTTPException, status

from semantic_reasoning_agent.api.dependencies import get_conversation_service
from semantic_reasoning_agent.schemas.chat import ConversationCreateRequest, ConversationResponse
from semantic_reasoning_agent.services.conversation_service import (
    ConversationNotFoundError,
    ConversationService,
)


router = APIRouter()


@router.get("", response_model=list[ConversationResponse])
def list_conversations(
    conversation_service: ConversationService = Depends(get_conversation_service),
) -> list[ConversationResponse]:
    return conversation_service.list_conversations()


@router.post("", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
def create_conversation(
    payload: ConversationCreateRequest,
    conversation_service: ConversationService = Depends(get_conversation_service),
) -> ConversationResponse:
    return conversation_service.create_conversation(payload)


@router.get("/{conversation_id}", response_model=ConversationResponse)
def get_conversation(
    conversation_id: str,
    conversation_service: ConversationService = Depends(get_conversation_service),
) -> ConversationResponse:
    try:
        return conversation_service.get_conversation(conversation_id)
    except ConversationNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
