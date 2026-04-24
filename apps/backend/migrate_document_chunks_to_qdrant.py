from __future__ import annotations

from semantic_reasoning_agent.core.container import get_app_container
from semantic_reasoning_agent.documents.models import IndexedChunk
from semantic_reasoning_agent.persistence.models import (
    DocumentChunkORM,
    KnowledgePackDocumentORM,
    KnowledgePackORM,
)
from sqlalchemy import select


def run() -> None:
    container = get_app_container()
    database_manager = container.database_manager
    qdrant_service = container.qdrant_collection_service

    migrated_chunks = 0
    with database_manager.session() as session:
        packs = session.scalars(select(KnowledgePackORM)).all()
        for pack in packs:
            doc_ids = list(
                session.scalars(
                    select(KnowledgePackDocumentORM.document_id).where(
                        KnowledgePackDocumentORM.knowledge_pack_id == pack.id
                    )
                ).all()
            )
            for document_id in doc_ids:
                rows = session.scalars(
                    select(DocumentChunkORM).where(
                        DocumentChunkORM.workspace_id == pack.workspace_id,
                        DocumentChunkORM.document_id == document_id,
                    )
                ).all()
                chunks: list[IndexedChunk] = []
                for row in rows:
                    if not isinstance(row.embedding, list):
                        continue
                    chunks.append(
                        IndexedChunk(
                            chunk_id=row.chunk_id,
                            document_id=row.document_id,
                            workspace_id=row.workspace_id,
                            document_title=row.document_title,
                            document_type=row.document_type,
                            text=row.text,
                            chunk_index=row.chunk_index,
                            source_url=row.source_url,
                            parser_version=row.parser_version,
                            created_at=row.created_at,
                            embedding=row.embedding,
                            embedding_provider=row.embedding_provider,
                            embedding_model=row.embedding_model,
                            page_number=row.page_number,
                            section_title=row.section_title,
                            heading_path=row.heading_path,
                            table_index=row.table_index,
                            sheet_name=row.sheet_name,
                            detected_table_id=row.detected_table_id,
                            row_start=row.row_start,
                            row_end=row.row_end,
                            column_headers=list(row.column_headers or []),
                        )
                    )
                if not chunks:
                    continue
                qdrant_service.upsert_chunks(pack.workspace_id, pack.id, chunks)
                migrated_chunks += len(chunks)

    print(f"Migrated {migrated_chunks} chunks to Qdrant collections.")


if __name__ == "__main__":
    run()
