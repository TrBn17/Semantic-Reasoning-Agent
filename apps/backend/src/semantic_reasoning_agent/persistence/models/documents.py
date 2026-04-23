from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, LargeBinary, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from .base import Base, utc_now


class DocumentORM(Base):
    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    title: Mapped[str] = mapped_column(String(255))
    filename: Mapped[str] = mapped_column(String(255))
    workspace_id: Mapped[str] = mapped_column(String(64), index=True)
    document_type: Mapped[str] = mapped_column(String(32), index=True)
    status: Mapped[str] = mapped_column(String(32), index=True)
    parser_version: Mapped[str] = mapped_column(String(128))
    chunk_count: Mapped[int] = mapped_column(Integer, default=0)
    tags: Mapped[list[str]] = mapped_column(JSON, default=list)
    ingestion_options: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)
    ingestion_mode: Mapped[str] = mapped_column(String(32), default="both", index=True)
    source_url: Mapped[str] = mapped_column(Text)
    source_object_key: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_content_type: Mapped[str | None] = mapped_column(String(255), nullable=True)
    size_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    binary_content: Mapped[bytes] = mapped_column(LargeBinary)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    jobs: Mapped[list["DocumentJobORM"]] = relationship(
        back_populates="document",
        cascade="all, delete-orphan",
        order_by="DocumentJobORM.name",
    )
    chunks: Mapped[list["DocumentChunkORM"]] = relationship(
        back_populates="document",
        cascade="all, delete-orphan",
        order_by="DocumentChunkORM.chunk_index",
    )
    artifacts: Mapped[list["DocumentArtifactORM"]] = relationship(
        back_populates="document",
        cascade="all, delete-orphan",
        order_by="DocumentArtifactORM.created_at",
    )
    extraction_runs: Mapped[list["DocumentExtractionRunORM"]] = relationship(
        back_populates="document",
        cascade="all, delete-orphan",
        order_by="DocumentExtractionRunORM.created_at",
    )


class DocumentJobORM(Base):
    __tablename__ = "document_jobs"

    id: Mapped[str] = mapped_column(String(128), primary_key=True)
    document_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("documents.id", ondelete="CASCADE"),
        index=True,
    )
    name: Mapped[str] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(32), index=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    document: Mapped[DocumentORM] = relationship(back_populates="jobs")


class DocumentChunkORM(Base):
    __tablename__ = "document_chunks"

    chunk_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    document_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("documents.id", ondelete="CASCADE"),
        index=True,
    )
    workspace_id: Mapped[str] = mapped_column(String(64), index=True)
    document_title: Mapped[str] = mapped_column(String(255))
    document_type: Mapped[str] = mapped_column(String(32), index=True)
    text: Mapped[str] = mapped_column(Text)
    chunk_index: Mapped[int] = mapped_column(Integer)
    source_url: Mapped[str] = mapped_column(Text)
    parser_version: Mapped[str] = mapped_column(String(128))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    embedding: Mapped[list[float] | dict[str, int]] = mapped_column(JSON)
    embedding_provider: Mapped[str | None] = mapped_column(String(64), nullable=True)
    embedding_model: Mapped[str | None] = mapped_column(String(255), nullable=True)
    page_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    section_title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    heading_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    table_index: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sheet_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    detected_table_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    row_start: Mapped[int | None] = mapped_column(Integer, nullable=True)
    row_end: Mapped[int | None] = mapped_column(Integer, nullable=True)
    column_headers: Mapped[list[str]] = mapped_column(JSON, default=list)

    document: Mapped[DocumentORM] = relationship(back_populates="chunks")


class OntologySearchIndexORM(Base):
    __tablename__ = "ontology_search_index"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    workspace_id: Mapped[str] = mapped_column(String(64), index=True)
    version_id: Mapped[str] = mapped_column(String(64), index=True)
    item_type: Mapped[str] = mapped_column(String(32), index=True)
    item_id: Mapped[str] = mapped_column(String(64), index=True)
    title: Mapped[str] = mapped_column(String(255))
    content: Mapped[str] = mapped_column(Text)
    embedding: Mapped[list[float] | dict[str, int]] = mapped_column(JSON)
    embedding_provider: Mapped[str] = mapped_column(String(64))
    embedding_model: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class DocumentArtifactORM(Base):
    __tablename__ = "document_artifacts"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    document_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("documents.id", ondelete="CASCADE"),
        index=True,
    )
    workspace_id: Mapped[str] = mapped_column(String(64), index=True)
    artifact_type: Mapped[str] = mapped_column(String(64), index=True)
    name: Mapped[str] = mapped_column(String(255))
    object_key: Mapped[str] = mapped_column(Text)
    public_url: Mapped[str] = mapped_column(Text)
    content_type: Mapped[str] = mapped_column(String(255))
    size_bytes: Mapped[int] = mapped_column(Integer, default=0)
    metadata_json: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    document: Mapped[DocumentORM] = relationship(back_populates="artifacts")


class DocumentExtractionRunORM(Base):
    __tablename__ = "document_extraction_runs"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    document_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("documents.id", ondelete="CASCADE"),
        index=True,
    )
    workspace_id: Mapped[str] = mapped_column(String(64), index=True)
    status: Mapped[str] = mapped_column(String(32), index=True)
    schema_json: Mapped[dict[str, object]] = mapped_column(JSON)
    result_json: Mapped[dict[str, object] | None] = mapped_column(JSON, nullable=True)
    parser_version: Mapped[str | None] = mapped_column(String(128), nullable=True)
    use_llm: Mapped[bool] = mapped_column(default=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    document: Mapped[DocumentORM] = relationship(back_populates="extraction_runs")
