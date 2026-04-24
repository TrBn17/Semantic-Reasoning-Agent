import re

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text

from semantic_reasoning_agent.core.config import get_settings
from semantic_reasoning_agent.entrypoints.dependencies import get_database_manager
from semantic_reasoning_agent.persistence.database import DatabaseManager
from semantic_reasoning_agent.schemas.auth import (
    AuthMeResponse,
    WorkspaceCreateRequest,
    WorkspaceSummary,
    WorkspaceUpdateRequest,
)


router = APIRouter()

WORKSPACE_USAGE_QUERIES = (
    "SELECT COUNT(*) FROM ontology_builds WHERE workspace_id = :workspace_id",
    "SELECT COUNT(*) FROM documents WHERE workspace_id = :workspace_id",
    "SELECT COUNT(*) FROM conversations WHERE workspace_id = :workspace_id",
    "SELECT COUNT(*) FROM provider_configs WHERE workspace_id = :workspace_id",
    "SELECT COUNT(*) FROM search_tool_configs WHERE workspace_id = :workspace_id",
    "SELECT COUNT(*) FROM knowledge_packs WHERE workspace_id = :workspace_id",
)


def _ensure_workspace_registry(session) -> None:
    session.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS workspace_registry (
                workspace_id VARCHAR(64) PRIMARY KEY,
                workspace_name VARCHAR(128) NOT NULL,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
    )


def _load_workspace_names(session) -> dict[str, str]:
    _ensure_workspace_registry(session)
    rows = session.execute(
        text("SELECT workspace_id, workspace_name FROM workspace_registry")
    ).mappings()
    return {row["workspace_id"]: row["workspace_name"] for row in rows}


def _workspace_has_data(session, workspace_id: str) -> bool:
    for query in WORKSPACE_USAGE_QUERIES:
        try:
            count = session.execute(
                text(query), {"workspace_id": workspace_id}
            ).scalar_one()
        except Exception:
            continue
        if count and int(count) > 0:
            return True
    return False


def _collect_workspaces(settings, session) -> dict[str, str]:
    workspaces: dict[str, str] = {
        settings.default_workspace_id: settings.default_workspace_name
    }
    registry_names = _load_workspace_names(session)
    workspaces.update(registry_names)
    return workspaces


def _slugify_workspace_id(name: str) -> str:
    candidate = re.sub(r"[^a-z0-9]+", "-", name.strip().lower()).strip("-")
    return candidate or "workspace"


def _generate_workspace_id(name: str, existing_ids: set[str]) -> str:
    base = _slugify_workspace_id(name)[:64]
    if base not in existing_ids:
        return base

    suffix = 2
    while True:
        suffix_text = f"-{suffix}"
        truncated_base = base[: 64 - len(suffix_text)]
        candidate = f"{truncated_base}{suffix_text}"
        if candidate not in existing_ids:
            return candidate
        suffix += 1


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
    with db_manager.session() as session:
        workspaces = _collect_workspaces(settings, session)
    return [
        WorkspaceSummary(id=ws_id, name=ws_name)
        for ws_id, ws_name in sorted(workspaces.items(), key=lambda item: item[1].lower())
    ]


@router.post(
    "/workspaces",
    response_model=WorkspaceSummary,
    status_code=status.HTTP_201_CREATED,
)
def create_workspace(
    payload: WorkspaceCreateRequest,
    db_manager: DatabaseManager = Depends(get_database_manager),
) -> WorkspaceSummary:
    workspace_name = payload.name.strip()
    if not workspace_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Workspace name is required.",
        )

    settings = get_settings()
    with db_manager.session() as session:
        existing = _collect_workspaces(settings, session)
        workspace_id = _generate_workspace_id(workspace_name, set(existing.keys()))

        session.execute(
            text(
                """
                INSERT INTO workspace_registry (workspace_id, workspace_name, updated_at)
                VALUES (:workspace_id, :workspace_name, CURRENT_TIMESTAMP)
                """
            ),
            {"workspace_id": workspace_id, "workspace_name": workspace_name},
        )
        session.commit()

    return WorkspaceSummary(id=workspace_id, name=workspace_name)


@router.patch("/workspaces/{workspace_id}", response_model=WorkspaceSummary)
def update_workspace(
    workspace_id: str,
    payload: WorkspaceUpdateRequest,
    db_manager: DatabaseManager = Depends(get_database_manager),
) -> WorkspaceSummary:
    workspace_name = payload.name.strip()
    if not workspace_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Workspace name is required.",
        )

    settings = get_settings()
    with db_manager.session() as session:
        existing = _collect_workspaces(settings, session)
        if workspace_id not in existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workspace not found.",
            )

        _ensure_workspace_registry(session)
        row = session.execute(
            text(
                "SELECT workspace_id FROM workspace_registry WHERE workspace_id = :workspace_id"
            ),
            {"workspace_id": workspace_id},
        ).first()
        if row is None:
            session.execute(
                text(
                    """
                    INSERT INTO workspace_registry (workspace_id, workspace_name, updated_at)
                    VALUES (:workspace_id, :workspace_name, CURRENT_TIMESTAMP)
                    """
                ),
                {"workspace_id": workspace_id, "workspace_name": workspace_name},
            )
        else:
            session.execute(
                text(
                    """
                    UPDATE workspace_registry
                    SET workspace_name = :workspace_name, updated_at = CURRENT_TIMESTAMP
                    WHERE workspace_id = :workspace_id
                    """
                ),
                {"workspace_id": workspace_id, "workspace_name": workspace_name},
            )
        session.commit()

    return WorkspaceSummary(id=workspace_id, name=workspace_name)


@router.delete("/workspaces/{workspace_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_workspace(
    workspace_id: str,
    db_manager: DatabaseManager = Depends(get_database_manager),
) -> None:
    settings = get_settings()
    if workspace_id == settings.default_workspace_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Default workspace cannot be deleted.",
        )

    with db_manager.session() as session:
        _ensure_workspace_registry(session)
        existing_registry = session.execute(
            text(
                "SELECT workspace_id FROM workspace_registry WHERE workspace_id = :workspace_id"
            ),
            {"workspace_id": workspace_id},
        ).first()
        if existing_registry is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workspace not found.",
            )
        if _workspace_has_data(session, workspace_id):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Workspace has existing data and cannot be deleted.",
            )

        session.execute(
            text("DELETE FROM workspace_registry WHERE workspace_id = :workspace_id"),
            {"workspace_id": workspace_id},
        )
        session.commit()
