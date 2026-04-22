from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from semantic_reasoning_agent.persistence.database import DatabaseManager
from semantic_reasoning_agent.persistence.models import (
    DocumentORM,
    KnowledgePackDocumentORM,
    KnowledgePackORM,
)
from semantic_reasoning_agent.schemas.knowledge_packs import (
    KnowledgePackCreateRequest,
    KnowledgePackResponse,
    KnowledgePackUpdateRequest,
)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class KnowledgePackNotFoundError(ValueError):
    """Raised when a knowledge pack id does not exist."""


class KnowledgePackValidationError(ValueError):
    """Raised when a knowledge pack payload references invalid documents."""


class KnowledgePackService:
    def __init__(self, database_manager: DatabaseManager) -> None:
        self._database_manager = database_manager

    def list_packs(self, workspace_id: str | None = None) -> list[KnowledgePackResponse]:
        with self._database_manager.session() as session:
            statement = select(KnowledgePackORM).options(selectinload(KnowledgePackORM.documents))
            if workspace_id:
                statement = statement.where(KnowledgePackORM.workspace_id == workspace_id)
            packs = session.scalars(statement).all()
            packs.sort(key=lambda item: item.name.lower())
            return [self._to_schema(pack) for pack in packs]

    def create_pack(self, payload: KnowledgePackCreateRequest) -> KnowledgePackResponse:
        pack_id = str(uuid4())
        now = utc_now()
        with self._database_manager.session() as session:
            self._validate_document_ids(session, payload.workspace_id, payload.document_ids)
            pack = KnowledgePackORM(
                id=pack_id,
                workspace_id=payload.workspace_id,
                name=payload.name,
                description=payload.description,
                status=payload.status,
                created_at=now,
                updated_at=now,
            )
            session.add(pack)
            session.flush()
            self._replace_documents(session, pack_id, payload.document_ids)
        return self.get_pack(pack_id)

    def get_pack(self, pack_id: str) -> KnowledgePackResponse:
        with self._database_manager.session() as session:
            pack = session.scalar(
                select(KnowledgePackORM)
                .options(selectinload(KnowledgePackORM.documents))
                .where(KnowledgePackORM.id == pack_id)
            )
            if pack is None:
                raise KnowledgePackNotFoundError(f"Knowledge pack '{pack_id}' was not found.")
            return self._to_schema(pack)

    def update_pack(self, pack_id: str, payload: KnowledgePackUpdateRequest) -> KnowledgePackResponse:
        with self._database_manager.session() as session:
            pack = session.scalar(
                select(KnowledgePackORM)
                .options(selectinload(KnowledgePackORM.documents))
                .where(KnowledgePackORM.id == pack_id)
            )
            if pack is None:
                raise KnowledgePackNotFoundError(f"Knowledge pack '{pack_id}' was not found.")

            if payload.name is not None:
                pack.name = payload.name
            if payload.description is not None:
                pack.description = payload.description
            if payload.status is not None:
                pack.status = payload.status
            if payload.document_ids is not None:
                self._validate_document_ids(session, pack.workspace_id, payload.document_ids)
                self._replace_documents(session, pack_id, payload.document_ids)
            pack.updated_at = utc_now()
        return self.get_pack(pack_id)

    def resolve_document_scope(
        self,
        workspace_id: str,
        knowledge_pack_ids: list[str],
    ) -> list[str]:
        if not knowledge_pack_ids:
            return []
        with self._database_manager.session() as session:
            pack_rows = session.scalars(
                select(KnowledgePackORM)
                .options(selectinload(KnowledgePackORM.documents))
                .where(
                    KnowledgePackORM.workspace_id == workspace_id,
                    KnowledgePackORM.id.in_(knowledge_pack_ids),
                )
            ).all()
            document_ids: set[str] = set()
            for pack in pack_rows:
                for membership in pack.documents:
                    document_ids.add(membership.document_id)
            return sorted(document_ids)

    def _replace_documents(self, session, pack_id: str, document_ids: list[str]) -> None:
        existing = session.scalars(
            select(KnowledgePackDocumentORM).where(KnowledgePackDocumentORM.knowledge_pack_id == pack_id)
        ).all()
        for item in existing:
            session.delete(item)
        now = utc_now()
        for document_id in sorted(set(document_ids)):
            session.add(
                KnowledgePackDocumentORM(
                    knowledge_pack_id=pack_id,
                    document_id=document_id,
                    created_at=now,
                )
            )

    def _validate_document_ids(self, session, workspace_id: str, document_ids: list[str]) -> None:
        unique_ids = sorted(set(document_ids))
        if not unique_ids:
            return
        found = session.scalars(
            select(DocumentORM.id).where(
                DocumentORM.workspace_id == workspace_id,
                DocumentORM.id.in_(unique_ids),
            )
        ).all()
        missing = sorted(set(unique_ids) - set(found))
        if missing:
            raise KnowledgePackValidationError(
                "Knowledge pack documents must belong to the same workspace. "
                f"Unknown or out-of-scope document ids: {', '.join(missing)}"
            )

    @staticmethod
    def _to_schema(pack: KnowledgePackORM) -> KnowledgePackResponse:
        return KnowledgePackResponse(
            id=pack.id,
            workspace_id=pack.workspace_id,
            name=pack.name,
            description=pack.description,
            document_ids=[item.document_id for item in pack.documents],
            status=pack.status,
            created_at=pack.created_at,
            updated_at=pack.updated_at,
        )
