from fastapi import APIRouter, Depends, HTTPException, status

from semantic_reasoning_agent.entrypoints.dependencies import get_conversation_service
from semantic_reasoning_agent.schemas.chat import (
    ConversationAgentProfileRequest,
    ConversationCreateRequest,
    ConversationModelSelectionRequest,
    ConversationResponse,
)
from semantic_reasoning_agent.services.conversation_service import (
    ConversationNotFoundError,
    ConversationPolicyError,
    ConversationService,
)
from semantic_reasoning_agent.services.agent_profile_service import AgentProfileNotFoundError


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


@router.patch("/{conversation_id}/model-selection", response_model=ConversationResponse)
def update_model_selection(
    conversation_id: str,
    payload: ConversationModelSelectionRequest,
    conversation_service: ConversationService = Depends(get_conversation_service),
) -> ConversationResponse:
    try:
        return conversation_service.update_runtime_selection(conversation_id, payload)
    except ConversationNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ConversationPolicyError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.patch("/{conversation_id}/agent-profile", response_model=ConversationResponse)
def update_agent_profile(
    conversation_id: str,
    payload: ConversationAgentProfileRequest,
    conversation_service: ConversationService = Depends(get_conversation_service),
) -> ConversationResponse:
    try:
        return conversation_service.update_agent_profile(conversation_id, payload)
    except ConversationNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except AgentProfileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
