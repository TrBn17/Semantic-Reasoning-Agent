from uuid import uuid4

from sqlalchemy import delete, select

from semantic_reasoning_agent.core.config import Settings
from semantic_reasoning_agent.core.runtime_constants import DEFAULT_TASK_TOP_K
from semantic_reasoning_agent.core.time import utc_now
from semantic_reasoning_agent.documents.models import IndexedChunk, ParsedChunk
from semantic_reasoning_agent.persistence.database import DatabaseManager
from semantic_reasoning_agent.persistence.models import DocumentChunkORM
from semantic_reasoning_agent.infrastructure.vector import TokenVectorBackend
from semantic_reasoning_agent.ports.vector_backend import VectorBackendPort
from semantic_reasoning_agent.schemas.documents import DocumentResponse
from semantic_reasoning_agent.schemas.retrieval import Citation, RetrievalResult, RetrievalSearchResponse
from semantic_reasoning_agent.services.embedding_service import EmbeddingService
from semantic_reasoning_agent.services.model_config_service import ModelConfigService


class RetrievalService:
    def __init__(
        self,
        settings: Settings,
        database_manager: DatabaseManager,
        vector_backend: VectorBackendPort | None = None,
        model_config_service: ModelConfigService | None = None,
    ) -> None:
        self._settings = settings
        self._database_manager = database_manager
        self._vector_backend = vector_backend or TokenVectorBackend()
        self._embedding_service = (
            EmbeddingService(settings, model_config_service)
            if model_config_service is not None
            else None
        )

    def prepare_chunks(
        self,
        document: DocumentResponse,
        chunks: list[ParsedChunk],
        *,
        parser_version: str,
    ) -> list[IndexedChunk]:
        prepared_chunks: list[IndexedChunk] = []
        for chunk in chunks:
            embedding_record = self._embed_text(
                chunk.text,
                workspace_id=document.workspace_id,
            )
            prepared_chunks.append(
                IndexedChunk(
                    chunk_id=str(uuid4()),
                    document_id=document.id,
                    workspace_id=document.workspace_id,
                    document_title=document.title,
                    document_type=document.document_type,
                    text=chunk.text,
                    chunk_index=chunk.chunk_index,
                    source_url=document.source_url,
                    parser_version=parser_version,
                    created_at=utc_now(),
                    embedding=embedding_record.values,
                    embedding_provider=embedding_record.provider,
                    embedding_model=embedding_record.model,
                    page_number=chunk.page_number,
                    section_title=chunk.section_title,
                    heading_path=chunk.heading_path,
                    table_index=chunk.table_index,
                    sheet_name=chunk.sheet_name,
                    detected_table_id=chunk.detected_table_id,
                    row_start=chunk.row_start,
                    row_end=chunk.row_end,
                    column_headers=chunk.column_headers,
                )
            )
        return prepared_chunks

    def upsert_chunks(self, document_id: str, chunks: list[IndexedChunk]) -> None:
        with self._database_manager.session() as session:
            session.execute(delete(DocumentChunkORM).where(DocumentChunkORM.document_id == document_id))
            for chunk in chunks:
                session.add(
                    DocumentChunkORM(
                        chunk_id=chunk.chunk_id,
                        document_id=chunk.document_id,
                        workspace_id=chunk.workspace_id,
                        document_title=chunk.document_title,
                        document_type=chunk.document_type,
                        text=chunk.text,
                        chunk_index=chunk.chunk_index,
                        source_url=chunk.source_url,
                        parser_version=chunk.parser_version,
                        created_at=chunk.created_at,
                        embedding=chunk.embedding,
                        embedding_provider=chunk.embedding_provider,
                        embedding_model=chunk.embedding_model,
                        page_number=chunk.page_number,
                        section_title=chunk.section_title,
                        heading_path=chunk.heading_path,
                        table_index=chunk.table_index,
                        sheet_name=chunk.sheet_name,
                        detected_table_id=chunk.detected_table_id,
                        row_start=chunk.row_start,
                        row_end=chunk.row_end,
                        column_headers=chunk.column_headers,
                    )
                )

    def remove_document(self, document_id: str) -> None:
        with self._database_manager.session() as session:
            session.execute(delete(DocumentChunkORM).where(DocumentChunkORM.document_id == document_id))

    def search(
        self,
        query: str,
        workspace_id: str | None = None,
        document_ids: list[str] | None = None,
        top_k: int = DEFAULT_TASK_TOP_K,
        embedding_provider: str | None = None,
        embedding_model: str | None = None,
    ) -> RetrievalSearchResponse:
        resolved_workspace_id = workspace_id or self._settings.default_workspace_id
        with self._database_manager.session() as session:
            statement = select(DocumentChunkORM).where(DocumentChunkORM.workspace_id == resolved_workspace_id)
            if document_ids:
                statement = statement.where(DocumentChunkORM.document_id.in_(document_ids))
            chunks = session.scalars(statement).all()

        query_embedding = self._embed_text(
            query,
            workspace_id=resolved_workspace_id,
            provider=embedding_provider,
            model=embedding_model,
        )
        preferred_chunks = [
            chunk
            for chunk in chunks
            if (
                not embedding_provider
                or chunk.embedding_provider == query_embedding.provider
            )
            and (
                not embedding_model
                or chunk.embedding_model == query_embedding.model
            )
        ]
        chunks_to_score = preferred_chunks or chunks
        matches: list[tuple[DocumentChunkORM, float]] = []
        for chunk in chunks_to_score:
            score = self._cosine_similarity(query_embedding.values, chunk.embedding)
            if score <= 0:
                continue
            matches.append((chunk, score))
        matches.sort(key=lambda item: item[1], reverse=True)
        matches = matches[:top_k]

        results = [
            RetrievalResult(
                chunk_id=chunk.chunk_id,
                document_id=chunk.document_id,
                document_title=chunk.document_title,
                document_type=chunk.document_type,
                score=round(score, 6),
                excerpt=excerpt(chunk.text),
                citation=self._build_citation(chunk),
            )
            for chunk, score in matches
        ]
        return RetrievalSearchResponse(query=query, results=results)

    def embed_text(
        self,
        text: str,
        *,
        workspace_id: str | None = None,
        provider: str | None = None,
        model: str | None = None,
    ) -> list[float] | dict[str, int]:
        return self._embed_text(
            text,
            workspace_id=workspace_id,
            provider=provider,
            model=model,
        ).values

    def _embed_text(
        self,
        text: str,
        *,
        workspace_id: str | None = None,
        provider: str | None = None,
        model: str | None = None,
    ):
        if self._embedding_service is not None:
            return self._embedding_service.embed_text(
                text,
                workspace_id=workspace_id,
                provider=provider,
                model=model,
            )
        return type(
            "_TokenEmbeddingRecord",
            (),
            {
                "values": self._vector_backend.embed_text(text),
                "provider": provider or "token",
                "model": model or "token-fallback",
            },
        )()

    def _cosine_similarity(
        self,
        left: list[float] | dict[str, int],
        right: list[float] | dict[str, int],
    ) -> float:
        if self._embedding_service is not None:
            return self._embedding_service.cosine_similarity(left, right)
        if isinstance(left, dict) and isinstance(right, dict):
            return self._vector_backend.cosine_similarity(left, right)
        return 0.0

    def _build_citation(self, chunk: DocumentChunkORM) -> Citation:
        location_label = "document"
        if chunk.document_type == "pdf" and chunk.page_number is not None:
            location_label = f"page {chunk.page_number}"
        elif chunk.document_type == "docx" and chunk.heading_path:
            location_label = chunk.heading_path
        elif (
            chunk.document_type in {"xlsx", "csv"}
            and chunk.row_start is not None
            and chunk.row_end is not None
        ):
            prefix = f"{chunk.sheet_name} " if chunk.sheet_name else ""
            location_label = f"{prefix}rows {chunk.row_start}-{chunk.row_end}".strip()

        return Citation(
            chunk_id=chunk.chunk_id,
            document_id=chunk.document_id,
            document_title=chunk.document_title,
            document_type=chunk.document_type,
            excerpt=excerpt(chunk.text),
            location_label=location_label,
            source_url=chunk.source_url,
            page_number=chunk.page_number,
            heading_path=chunk.heading_path,
            sheet_name=chunk.sheet_name,
            row_start=chunk.row_start,
            row_end=chunk.row_end,
        )


def excerpt(text: str, limit: int = 240) -> str:
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."

