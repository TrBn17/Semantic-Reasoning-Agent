from __future__ import annotations

from sqlalchemy import select

from semantic_reasoning_agent.persistence.database import DatabaseManager
from semantic_reasoning_agent.persistence.models import DocumentORM


class DocumentRepository:
    def __init__(self, database_manager: DatabaseManager) -> None:
        self._database_manager = database_manager

    def get_by_id(self, document_id: str) -> DocumentORM | None:
        with self._database_manager.session() as session:
            return session.get(DocumentORM, document_id)

    def list_by_workspace(self, workspace_id: str) -> list[DocumentORM]:
        with self._database_manager.session() as session:
            return list(
                session.scalars(
                    select(DocumentORM).where(DocumentORM.workspace_id == workspace_id)
                )
            )
