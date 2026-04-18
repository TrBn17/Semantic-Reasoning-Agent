from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, Integer, LargeBinary, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.types import JSON


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    """Base class for ORM models."""


class ConversationORM(Base):
    __tablename__ = "conversations"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    title: Mapped[str] = mapped_column(String(255))
    provider: Mapped[str] = mapped_column(String(64))
    model: Mapped[str] = mapped_column(String(128))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    messages: Mapped[list["MessageORM"]] = relationship(
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="MessageORM.created_at",
    )


class MessageORM(Base):
    __tablename__ = "messages"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    conversation_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        index=True,
    )
    role: Mapped[str] = mapped_column(String(32))
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    conversation: Mapped[ConversationORM] = relationship(back_populates="messages")


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
    source_url: Mapped[str] = mapped_column(Text)
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
    embedding: Mapped[dict[str, int]] = mapped_column(JSON)
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


class OntologyBuildORM(Base):
    __tablename__ = "ontology_builds"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    document_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("documents.id", ondelete="CASCADE"),
        index=True,
    )
    workspace_id: Mapped[str] = mapped_column(String(64), index=True)
    status: Mapped[str] = mapped_column(String(32), index=True)
    domain: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    published_version_id: Mapped[str | None] = mapped_column(String(64), nullable=True)

    steps: Mapped[list["OntologyBuildStepORM"]] = relationship(
        back_populates="build",
        cascade="all, delete-orphan",
        order_by="OntologyBuildStepORM.name",
    )
    entities: Mapped[list["OntologyCandidateEntityORM"]] = relationship(
        back_populates="build",
        cascade="all, delete-orphan",
        order_by="OntologyCandidateEntityORM.canonical_name",
    )
    relations: Mapped[list["OntologyCandidateRelationORM"]] = relationship(
        back_populates="build",
        cascade="all, delete-orphan",
        order_by="OntologyCandidateRelationORM.relation_type",
    )


class OntologyBuildStepORM(Base):
    __tablename__ = "ontology_build_steps"

    id: Mapped[str] = mapped_column(String(128), primary_key=True)
    build_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("ontology_builds.id", ondelete="CASCADE"),
        index=True,
    )
    name: Mapped[str] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(32), index=True)
    detail: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    build: Mapped[OntologyBuildORM] = relationship(back_populates="steps")


class OntologyCandidateEntityORM(Base):
    __tablename__ = "ontology_candidate_entities"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    build_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("ontology_builds.id", ondelete="CASCADE"),
        index=True,
    )
    document_id: Mapped[str] = mapped_column(String(64), index=True)
    workspace_id: Mapped[str] = mapped_column(String(64), index=True)
    name: Mapped[str] = mapped_column(String(255))
    canonical_name: Mapped[str] = mapped_column(String(255))
    resolution_key: Mapped[str] = mapped_column(String(255), index=True)
    entity_type: Mapped[str] = mapped_column(String(64))
    confidence: Mapped[float] = mapped_column(Float)
    status: Mapped[str] = mapped_column(String(32), index=True)
    source_chunk_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    evidence_text: Mapped[str] = mapped_column(Text)
    provenance: Mapped[dict] = mapped_column(JSON, default=dict)
    aliases: Mapped[list[str]] = mapped_column(JSON, default=list)
    merged_into_entity_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    build: Mapped[OntologyBuildORM] = relationship(back_populates="entities")


class OntologyCandidateRelationORM(Base):
    __tablename__ = "ontology_candidate_relations"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    build_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("ontology_builds.id", ondelete="CASCADE"),
        index=True,
    )
    document_id: Mapped[str] = mapped_column(String(64), index=True)
    workspace_id: Mapped[str] = mapped_column(String(64), index=True)
    source_entity_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    target_entity_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    source_name: Mapped[str] = mapped_column(String(255))
    target_name: Mapped[str] = mapped_column(String(255))
    relation_type: Mapped[str] = mapped_column(String(64))
    confidence: Mapped[float] = mapped_column(Float)
    status: Mapped[str] = mapped_column(String(32), index=True)
    source_chunk_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    evidence_text: Mapped[str] = mapped_column(Text)
    provenance: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    build: Mapped[OntologyBuildORM] = relationship(back_populates="relations")


class OntologyVersionORM(Base):
    __tablename__ = "ontology_versions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    workspace_id: Mapped[str] = mapped_column(String(64), index=True)
    version_number: Mapped[int] = mapped_column(Integer)
    source_build_id: Mapped[str] = mapped_column(String(64), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    entities: Mapped[list["OntologyEntityORM"]] = relationship(
        back_populates="version",
        cascade="all, delete-orphan",
        order_by="OntologyEntityORM.name",
    )
    relations: Mapped[list["OntologyRelationORM"]] = relationship(
        back_populates="version",
        cascade="all, delete-orphan",
        order_by="OntologyRelationORM.relation_type",
    )


class OntologyEntityORM(Base):
    __tablename__ = "ontology_entities"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    version_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("ontology_versions.id", ondelete="CASCADE"),
        index=True,
    )
    workspace_id: Mapped[str] = mapped_column(String(64), index=True)
    resolution_key: Mapped[str] = mapped_column(String(255), index=True)
    name: Mapped[str] = mapped_column(String(255))
    entity_type: Mapped[str] = mapped_column(String(64))
    aliases: Mapped[list[str]] = mapped_column(JSON, default=list)
    source_build_id: Mapped[str] = mapped_column(String(64), index=True)
    source_document_id: Mapped[str] = mapped_column(String(64), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    version: Mapped[OntologyVersionORM] = relationship(back_populates="entities")


class OntologyRelationORM(Base):
    __tablename__ = "ontology_relations"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    version_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("ontology_versions.id", ondelete="CASCADE"),
        index=True,
    )
    workspace_id: Mapped[str] = mapped_column(String(64), index=True)
    source_entity_id: Mapped[str] = mapped_column(String(64), index=True)
    target_entity_id: Mapped[str] = mapped_column(String(64), index=True)
    relation_type: Mapped[str] = mapped_column(String(64))
    confidence: Mapped[float] = mapped_column(Float)
    source_build_id: Mapped[str] = mapped_column(String(64), index=True)
    source_document_id: Mapped[str] = mapped_column(String(64), index=True)
    evidence_text: Mapped[str] = mapped_column(Text)
    provenance: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    version: Mapped[OntologyVersionORM] = relationship(back_populates="relations")
