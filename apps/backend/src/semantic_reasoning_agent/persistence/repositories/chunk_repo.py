from __future__ import annotations

from sqlalchemy import select

from semantic_reasoning_agent.persistence.database import DatabaseManager
from semantic_reasoning_agent.persistence.models import DocumentChunkORM


class ChunkRepository:
    def __init__(self, database_manager: DatabaseManager) -> None:
        self._database_manager = database_manager

    def list_by_document(self, document_id: str) -> list[DocumentChunkORM]:
        with self._database_manager.session() as session:
            return list(
                session.scalars(
                    select(DocumentChunkORM).where(
                        DocumentChunkORM.document_id == document_id
                    )
                )
            )

    def list_by_workspace(self, workspace_id: str) -> list[DocumentChunkORM]:
        with self._database_manager.session() as session:
            return list(
                session.scalars(
                    select(DocumentChunkORM).where(
                        DocumentChunkORM.workspace_id == workspace_id
                    )
                )
            )
