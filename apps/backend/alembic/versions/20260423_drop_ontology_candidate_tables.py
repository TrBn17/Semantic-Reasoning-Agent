"""Drop persisted ontology candidate tables.

Revision ID: 20260423_drop_ontology_candidate_tables
Revises: 20260423_add_search_tool_instances_and_embeddings
Create Date: 2026-04-23 23:55:00.000000
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260423_drop_ontology_candidate_tables"
down_revision: str | Sequence[str] | None = "20260423_add_search_tool_instances_and_embeddings"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_index(
        op.f("ix_ontology_candidate_relations_workspace_id"),
        table_name="ontology_candidate_relations",
    )
    op.drop_index(
        op.f("ix_ontology_candidate_relations_status"),
        table_name="ontology_candidate_relations",
    )
    op.drop_index(
        op.f("ix_ontology_candidate_relations_document_id"),
        table_name="ontology_candidate_relations",
    )
    op.drop_index(
        op.f("ix_ontology_candidate_relations_build_id"),
        table_name="ontology_candidate_relations",
    )
    op.drop_table("ontology_candidate_relations")

    op.drop_index(
        op.f("ix_ontology_candidate_entities_workspace_id"),
        table_name="ontology_candidate_entities",
    )
    op.drop_index(
        op.f("ix_ontology_candidate_entities_status"),
        table_name="ontology_candidate_entities",
    )
    op.drop_index(
        op.f("ix_ontology_candidate_entities_resolution_key"),
        table_name="ontology_candidate_entities",
    )
    op.drop_index(
        op.f("ix_ontology_candidate_entities_document_id"),
        table_name="ontology_candidate_entities",
    )
    op.drop_index(
        op.f("ix_ontology_candidate_entities_build_id"),
        table_name="ontology_candidate_entities",
    )
    op.drop_table("ontology_candidate_entities")


def downgrade() -> None:
    op.create_table(
        "ontology_candidate_entities",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("build_id", sa.String(length=64), nullable=False),
        sa.Column("document_id", sa.String(length=64), nullable=False),
        sa.Column("workspace_id", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("canonical_name", sa.String(length=255), nullable=False),
        sa.Column("resolution_key", sa.String(length=255), nullable=False),
        sa.Column("entity_type", sa.String(length=64), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("source_chunk_id", sa.String(length=64), nullable=True),
        sa.Column("evidence_text", sa.Text(), nullable=False),
        sa.Column("provenance", sa.JSON(), nullable=False),
        sa.Column("query_rules", sa.JSON(), nullable=False),
        sa.Column("facts", sa.JSON(), nullable=False),
        sa.Column("aliases", sa.JSON(), nullable=False),
        sa.Column("merged_into_entity_id", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["build_id"], ["ontology_builds.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_ontology_candidate_entities_build_id"),
        "ontology_candidate_entities",
        ["build_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_ontology_candidate_entities_document_id"),
        "ontology_candidate_entities",
        ["document_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_ontology_candidate_entities_resolution_key"),
        "ontology_candidate_entities",
        ["resolution_key"],
        unique=False,
    )
    op.create_index(
        op.f("ix_ontology_candidate_entities_status"),
        "ontology_candidate_entities",
        ["status"],
        unique=False,
    )
    op.create_index(
        op.f("ix_ontology_candidate_entities_workspace_id"),
        "ontology_candidate_entities",
        ["workspace_id"],
        unique=False,
    )

    op.create_table(
        "ontology_candidate_relations",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("build_id", sa.String(length=64), nullable=False),
        sa.Column("document_id", sa.String(length=64), nullable=False),
        sa.Column("workspace_id", sa.String(length=64), nullable=False),
        sa.Column("source_entity_id", sa.String(length=64), nullable=True),
        sa.Column("target_entity_id", sa.String(length=64), nullable=True),
        sa.Column("source_name", sa.String(length=255), nullable=False),
        sa.Column("target_name", sa.String(length=255), nullable=False),
        sa.Column("relation_type", sa.String(length=64), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("source_chunk_id", sa.String(length=64), nullable=True),
        sa.Column("evidence_text", sa.Text(), nullable=False),
        sa.Column("provenance", sa.JSON(), nullable=False),
        sa.Column("query_rules", sa.JSON(), nullable=False),
        sa.Column("facts", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["build_id"], ["ontology_builds.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_ontology_candidate_relations_build_id"),
        "ontology_candidate_relations",
        ["build_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_ontology_candidate_relations_document_id"),
        "ontology_candidate_relations",
        ["document_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_ontology_candidate_relations_status"),
        "ontology_candidate_relations",
        ["status"],
        unique=False,
    )
    op.create_index(
        op.f("ix_ontology_candidate_relations_workspace_id"),
        "ontology_candidate_relations",
        ["workspace_id"],
        unique=False,
    )
