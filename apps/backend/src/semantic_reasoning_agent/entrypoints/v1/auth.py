from fastapi import APIRouter, Depends
from sqlalchemy import text

from semantic_reasoning_agent.core.config import get_settings
from semantic_reasoning_agent.entrypoints.dependencies import get_database_manager
from semantic_reasoning_agent.persistence.database import DatabaseManager
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


@router.get("/workspaces", response_model=list[WorkspaceSummary])
def list_workspaces(
    db_manager: DatabaseManager = Depends(get_database_manager),
) -> list[WorkspaceSummary]:
    settings = get_settings()
    # Danh sách workspace mặc định
    workspaces = {
        settings.default_workspace_id: settings.default_workspace_name,
    }

    # Lấy thêm các workspace_id khác từ database bằng cách union các bảng chính
    with db_manager.session() as session:
        # Chúng ta dùng query SQL đơn giản để quét nhanh các workspace_id hiện có
        queries = [
            "SELECT DISTINCT workspace_id FROM ontology_builds",
            "SELECT DISTINCT workspace_id FROM documents",
            "SELECT DISTINCT workspace_id FROM conversations",
            "SELECT DISTINCT workspace_id FROM provider_configs",
        ]
        for q in queries:
            try:
                results = session.execute(text(q)).scalars().all()
                for ws_id in results:
                    if ws_id and ws_id not in workspaces:
                        workspaces[ws_id] = ws_id # Dùng ID làm tên nếu không có bảng mapping
            except Exception:
                continue

    return [
        WorkspaceSummary(id=ws_id, name=ws_name)
        for ws_id, ws_name in workspaces.items()
    ]
