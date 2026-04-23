from __future__ import annotations

from sqlalchemy import select

from semantic_reasoning_agent.core.container import get_app_container
from semantic_reasoning_agent.persistence.models import DocumentChunkORM


def test_ontology_mode_skips_chunk_indexing(document_service) -> None:  # noqa: ANN001
    document = document_service.upload_document(
        filename="ontology-only.csv",
        content=b"id,name\n1,Alpha\n2,Beta\n",
        ingestion_mode="ontology",
        content_type="text/csv",
    )
    refreshed = document_service.get_document(document.id)
    jobs = document_service.get_document_jobs(document.id)

    assert refreshed.status.value == "indexed"
    assert refreshed.ingestion_mode == "ontology"
    assert refreshed.chunk_count == 0
    assert [job.name for job in jobs] == ["convert_markdown", "store_artifacts"]

    with get_app_container().database_manager.session() as session:
        stored_chunks = session.scalars(
            select(DocumentChunkORM).where(DocumentChunkORM.document_id == document.id)
        ).all()
    assert stored_chunks == []


def test_retrieval_mode_builds_chunks(document_service) -> None:  # noqa: ANN001
    document = document_service.upload_document(
        filename="retrieval-only.csv",
        content=b"id,name\n1,Alpha\n2,Beta\n",
        ingestion_mode="retrieval",
        content_type="text/csv",
    )
    refreshed = document_service.get_document(document.id)
    jobs = document_service.get_document_jobs(document.id)

    assert refreshed.status.value == "indexed"
    assert refreshed.ingestion_mode == "retrieval"
    assert refreshed.chunk_count > 0
    assert [job.name for job in jobs] == [
        "convert_markdown",
        "store_artifacts",
        "build_chunks",
        "index_chunks",
    ]
