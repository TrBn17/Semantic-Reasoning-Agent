from fastapi import APIRouter, Depends, HTTPException, Query, status

from semantic_reasoning_agent.entrypoints.dependencies import get_agent_profile_service
from semantic_reasoning_agent.schemas.agent_profiles import (
    AgentProfileCreateRequest,
    AgentProfileResponse,
    AgentProfileUpdateRequest,
)
from semantic_reasoning_agent.services.agent_profile_service import (
    AgentProfileNotFoundError,
    AgentProfileService,
    AgentProfileValidationError,
)


router = APIRouter()


@router.get("", response_model=list[AgentProfileResponse])
def list_profiles(
    workspace_id: str | None = Query(default=None),
    agent_profile_service: AgentProfileService = Depends(get_agent_profile_service),
) -> list[AgentProfileResponse]:
    return agent_profile_service.list_profiles(workspace_id)


@router.post("", response_model=AgentProfileResponse, status_code=status.HTTP_201_CREATED)
def create_profile(
    payload: AgentProfileCreateRequest,
    agent_profile_service: AgentProfileService = Depends(get_agent_profile_service),
) -> AgentProfileResponse:
    try:
        return agent_profile_service.create_profile(payload)
    except AgentProfileValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/{profile_id}", response_model=AgentProfileResponse)
def get_profile(
    profile_id: str,
    agent_profile_service: AgentProfileService = Depends(get_agent_profile_service),
) -> AgentProfileResponse:
    try:
        return agent_profile_service.get_profile(profile_id)
    except AgentProfileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.patch("/{profile_id}", response_model=AgentProfileResponse)
def update_profile(
    profile_id: str,
    payload: AgentProfileUpdateRequest,
    agent_profile_service: AgentProfileService = Depends(get_agent_profile_service),
) -> AgentProfileResponse:
    try:
        return agent_profile_service.update_profile(profile_id, payload)
    except AgentProfileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except AgentProfileValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/{profile_id}/set-default", response_model=AgentProfileResponse)
def set_default_profile(
    profile_id: str,
    agent_profile_service: AgentProfileService = Depends(get_agent_profile_service),
) -> AgentProfileResponse:
    try:
        return agent_profile_service.set_default_profile(profile_id)
    except AgentProfileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
