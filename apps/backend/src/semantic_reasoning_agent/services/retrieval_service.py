from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import delete, select

from semantic_reasoning_agent.core.config import Settings
from semantic_reasoning_agent.persistence.database import DatabaseManager
from semantic_reasoning_agent.persistence.models.documents import DocumentChunkORM
from semantic_reasoning_agent.infrastructure.vector import TokenVectorBackend
from semantic_reasoning_agent.ports.vector_backend import VectorBackendPort
from semantic_reasoning_agent.infrastructure.parsers.models import IndexedChunk, ParsedDocument
from semantic_reasoning_agent.schemas.documents import DocumentResponse
from semantic_reasoning_agent.schemas.retrieval import Citation, RetrievalResult, RetrievalSearchResponse

def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class RetrievalService:
    def __init__(
        self,
        settings: Settings,
        database_manager: DatabaseManager,
        vector_backend: VectorBackendPort | None = None,
    ) -> None:
        self._settings = settings
        self._database_manager = database_manager
        self._vector_backend = vector_backend or TokenVectorBackend()

    def prepare_document_chunks(
        self,
        document: DocumentResponse,
        parsed_document: ParsedDocument,
    ) -> list[IndexedChunk]:
        prepared_chunks: list[IndexedChunk] = []
        for chunk in parsed_document.chunks:
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
                    parser_version=parsed_document.parser_version,
                    created_at=utc_now(),
                    embedding=self.embed_text(chunk.text),
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
        top_k: int = 3,
    ) -> RetrievalSearchResponse:
        resolved_workspace_id = workspace_id or self._settings.default_workspace_id
        with self._database_manager.session() as session:
            statement = select(DocumentChunkORM).where(DocumentChunkORM.workspace_id == resolved_workspace_id)
            if document_ids:
                statement = statement.where(DocumentChunkORM.document_id.in_(document_ids))
            chunks = session.scalars(statement).all()

        query_embedding = self.embed_text(query)
        matches: list[tuple[DocumentChunkORM, float]] = []
        for chunk in chunks:
            score = self._vector_backend.cosine_similarity(query_embedding, chunk.embedding)
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

    def embed_text(self, text: str) -> dict[str, int]:
        return self._vector_backend.embed_text(text)

    def _build_citation(self, chunk: DocumentChunkORM) -> Citation:
        location_label = "document"
        if chunk.document_type == "pdf" and chunk.page_number is not None:
            location_label = f"page {chunk.page_number}"
        elif chunk.document_type == "docx" and chunk.heading_path:
            location_label = chunk.heading_path
        elif (
            chunk.document_type == "xlsx"
            and chunk.sheet_name
            and chunk.row_start is not None
            and chunk.row_end is not None
        ):
            location_label = f"{chunk.sheet_name} rows {chunk.row_start}-{chunk.row_end}"

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

