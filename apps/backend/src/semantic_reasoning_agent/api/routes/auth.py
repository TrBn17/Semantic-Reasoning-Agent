from fastapi import APIRouter

from semantic_reasoning_agent.config import get_settings
from semantic_reasoning_agent.schemas.auth import AuthMeResponse, WorkspaceSummary


router = APIRouter()


@router.get("/me", response_model=AuthMeResponse)
def get_me() -> AuthMeResponse:
    settings = get_settings()
    return AuthMeResponse(
        id=settings.default_user_id,
        email=settings.default_user_email,
        display_name=settings.default_user_name,
        active_workspace=WorkspaceSummary(
            id=settings.default_workspace_id,
            name=settings.default_workspace_name,
        ),
    )
