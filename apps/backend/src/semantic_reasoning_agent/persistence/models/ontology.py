from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from .base import Base, utc_now


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
    architecture_draft_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)

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
    architecture_draft_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
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
    architecture_draft_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
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


class OntologyArchitectureDraftORM(Base):
    __tablename__ = "ontology_architecture_drafts"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    workspace_id: Mapped[str] = mapped_column(String(64), index=True)
    source_document_ids: Mapped[list[str]] = mapped_column(JSON, default=list)
    source_build_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    domain: Mapped[str] = mapped_column(String(64), index=True)
    status: Mapped[str] = mapped_column(String(32), index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    entity_types: Mapped[list[dict]] = mapped_column(JSON, default=list)
    relation_types: Mapped[list[dict]] = mapped_column(JSON, default=list)
    normalization_hints: Mapped[list[dict]] = mapped_column(JSON, default=list)
    workflow_hints: Mapped[list[str]] = mapped_column(JSON, default=list)
    tool_affinity_hints: Mapped[list[str]] = mapped_column(JSON, default=list)
    review_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    review_findings: Mapped[list[dict]] = mapped_column(JSON, default=list)
    provenance: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    evidence_links: Mapped[list["OntologyArchitectureEvidenceLinkORM"]] = relationship(
        back_populates="draft",
        cascade="all, delete-orphan",
        order_by="OntologyArchitectureEvidenceLinkORM.created_at",
    )


class OntologyArchitectureEvidenceLinkORM(Base):
    __tablename__ = "ontology_architecture_evidence_links"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    draft_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("ontology_architecture_drafts.id", ondelete="CASCADE"),
        index=True,
    )
    workspace_id: Mapped[str] = mapped_column(String(64), index=True)
    source_document_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    source_chunk_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    link_kind: Mapped[str] = mapped_column(String(32), index=True)
    target_name: Mapped[str] = mapped_column(String(128), index=True)
    evidence_text: Mapped[str] = mapped_column(Text)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    draft: Mapped[OntologyArchitectureDraftORM] = relationship(back_populates="evidence_links")
