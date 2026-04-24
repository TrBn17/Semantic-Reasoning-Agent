from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from semantic_reasoning_agent.persistence.database import DatabaseManager
from semantic_reasoning_agent.persistence.models import (
    DocumentChunkORM,
    DocumentORM,
    KnowledgePackDocumentORM,
    KnowledgePackORM,
)
from semantic_reasoning_agent.schemas.knowledge_packs import (
    KnowledgePackAddDocumentRequest,
    KnowledgePackCreateRequest,
    KnowledgePackDocumentSummaryResponse,
    KnowledgePackResponse,
    KnowledgePackUpdateRequest,
)
from semantic_reasoning_agent.services.qdrant_collection_service import (
    QdrantCollectionService,
    QdrantCollectionServiceError,
)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class KnowledgePackNotFoundError(ValueError):
    """Raised when a knowledge pack id does not exist."""


class KnowledgePackValidationError(ValueError):
    """Raised when a knowledge pack payload references invalid documents."""


class KnowledgePackService:
    def __init__(
        self,
        database_manager: DatabaseManager,
        qdrant_collection_service: QdrantCollectionService,
    ) -> None:
        self._database_manager = database_manager
        self._qdrant_collection_service = qdrant_collection_service

    def list_packs(self, workspace_id: str | None = None) -> list[KnowledgePackResponse]:
        with self._database_manager.session() as session:
            statement = select(KnowledgePackORM).options(selectinload(KnowledgePackORM.documents))
            if workspace_id:
                statement = statement.where(KnowledgePackORM.workspace_id == workspace_id)
            packs = session.scalars(statement).all()
            packs.sort(key=lambda item: item.name.lower())
            response: list[KnowledgePackResponse] = []
            for pack in packs:
                try:
                    documents = self._qdrant_collection_service.list_documents(pack.workspace_id, pack.id)
                except QdrantCollectionServiceError:
                    documents = []
                response.append(
                    self._to_schema(
                        pack,
                        document_ids=[item.document_id for item in documents],
                    )
                )
            return response

    def create_pack(self, payload: KnowledgePackCreateRequest) -> KnowledgePackResponse:
        pack_id = str(uuid4())
        now = utc_now()
        self._qdrant_collection_service.ensure_collection(payload.workspace_id, pack_id)
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
            if payload.document_ids:
                self._replace_documents(session, pack_id, payload.document_ids)
                self._copy_documents_to_collection(
                    session,
                    workspace_id=payload.workspace_id,
                    pack_id=pack_id,
                    document_ids=payload.document_ids,
                )
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
            try:
                documents = self._qdrant_collection_service.list_documents(pack.workspace_id, pack.id)
            except QdrantCollectionServiceError:
                documents = []
            return self._to_schema(
                pack,
                document_ids=[item.document_id for item in documents],
            )

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
                self._copy_documents_to_collection(
                    session,
                    workspace_id=pack.workspace_id,
                    pack_id=pack_id,
                    document_ids=payload.document_ids,
                )
            pack.updated_at = utc_now()
        return self.get_pack(pack_id)

    def delete_pack(self, pack_id: str) -> None:
        with self._database_manager.session() as session:
            pack = session.get(KnowledgePackORM, pack_id)
            if pack is None:
                raise KnowledgePackNotFoundError(f"Knowledge pack '{pack_id}' was not found.")
            workspace_id = pack.workspace_id
            session.delete(pack)
        self._qdrant_collection_service.delete_collection(workspace_id, pack_id)

    def list_pack_documents(self, pack_id: str) -> list[KnowledgePackDocumentSummaryResponse]:
        with self._database_manager.session() as session:
            pack = session.get(KnowledgePackORM, pack_id)
            if pack is None:
                raise KnowledgePackNotFoundError(f"Knowledge pack '{pack_id}' was not found.")
            try:
                docs = self._qdrant_collection_service.list_documents(pack.workspace_id, pack.id)
            except QdrantCollectionServiceError:
                docs = []
        return [
            KnowledgePackDocumentSummaryResponse(
                document_id=item.document_id,
                document_title=item.document_title,
                chunk_count=item.chunk_count,
            )
            for item in docs
        ]

    def add_document(
        self,
        pack_id: str,
        payload: KnowledgePackAddDocumentRequest,
    ) -> list[KnowledgePackDocumentSummaryResponse]:
        with self._database_manager.session() as session:
            pack = session.get(KnowledgePackORM, pack_id)
            if pack is None:
                raise KnowledgePackNotFoundError(f"Knowledge pack '{pack_id}' was not found.")
            self._validate_document_ids(session, pack.workspace_id, [payload.document_id])
            self._replace_documents(
                session,
                pack_id,
                sorted(set([payload.document_id, *self._pack_document_ids(session, pack_id)])),
            )
            self._copy_documents_to_collection(
                session,
                workspace_id=pack.workspace_id,
                pack_id=pack_id,
                document_ids=[payload.document_id],
            )
        return self.list_pack_documents(pack_id)

    def remove_document(self, pack_id: str, document_id: str) -> list[KnowledgePackDocumentSummaryResponse]:
        with self._database_manager.session() as session:
            pack = session.get(KnowledgePackORM, pack_id)
            if pack is None:
                raise KnowledgePackNotFoundError(f"Knowledge pack '{pack_id}' was not found.")
            members = self._pack_document_ids(session, pack_id)
            filtered = [item for item in members if item != document_id]
            self._replace_documents(session, pack_id, filtered)
            self._qdrant_collection_service.delete_document(pack.workspace_id, pack_id, document_id)
        return self.list_pack_documents(pack_id)

    def resolve_document_scope(
        self,
        workspace_id: str,
        knowledge_pack_ids: list[str],
    ) -> list[str]:
        if not knowledge_pack_ids:
            return []
        document_ids: set[str] = set()
        for pack_id in knowledge_pack_ids:
            try:
                documents = self._qdrant_collection_service.list_documents(workspace_id, pack_id)
            except QdrantCollectionServiceError:
                continue
            for item in documents:
                document_ids.add(item.document_id)
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

    def _pack_document_ids(self, session, pack_id: str) -> list[str]:
        return list(
            session.scalars(
                select(KnowledgePackDocumentORM.document_id).where(
                    KnowledgePackDocumentORM.knowledge_pack_id == pack_id
                )
            ).all()
        )

    def _copy_documents_to_collection(
        self,
        session,
        *,
        workspace_id: str,
        pack_id: str,
        document_ids: list[str],
    ) -> None:
        for document_id in sorted(set(document_ids)):
            cloned_points = self._qdrant_collection_service.collect_document_points_across_workspace(
                workspace_id=workspace_id,
                document_id=document_id,
                exclude_pack_id=pack_id,
            )
            if cloned_points:
                self._qdrant_collection_service.add_points_to_collection(
                    workspace_id=workspace_id,
                    knowledge_pack_id=pack_id,
                    points=cloned_points,
                )
                continue

            chunks = session.scalars(
                select(DocumentChunkORM).where(
                    DocumentChunkORM.workspace_id == workspace_id,
                    DocumentChunkORM.document_id == document_id,
                )
            ).all()
            if not chunks:
                continue
            self._qdrant_collection_service.ensure_collection(workspace_id, pack_id)
            points = []
            for chunk in chunks:
                if not isinstance(chunk.embedding, list):
                    continue
                points.append(
                    {
                        "id": chunk.chunk_id,
                        "vector": chunk.embedding,
                        "payload": {
                            "workspace_id": chunk.workspace_id,
                            "knowledge_pack_id": pack_id,
                            "document_id": chunk.document_id,
                            "document_title": chunk.document_title,
                            "document_type": chunk.document_type,
                            "text": chunk.text,
                            "chunk_index": chunk.chunk_index,
                            "source_url": chunk.source_url,
                            "parser_version": chunk.parser_version,
                            "embedding_provider": chunk.embedding_provider,
                            "embedding_model": chunk.embedding_model,
                            "page_number": chunk.page_number,
                            "heading_path": chunk.heading_path,
                            "sheet_name": chunk.sheet_name,
                            "row_start": chunk.row_start,
                            "row_end": chunk.row_end,
                        },
                    }
                )
            self._qdrant_collection_service.add_points_to_collection(
                workspace_id=workspace_id,
                knowledge_pack_id=pack_id,
                points=points,
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
    def _to_schema(pack: KnowledgePackORM, *, document_ids: list[str] | None = None) -> KnowledgePackResponse:
        return KnowledgePackResponse(
            id=pack.id,
            workspace_id=pack.workspace_id,
            name=pack.name,
            description=pack.description,
            document_ids=document_ids if document_ids is not None else [item.document_id for item in pack.documents],
            status=pack.status,
            created_at=pack.created_at,
            updated_at=pack.updated_at,
        )
