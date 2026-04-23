"""Add ontology query rules and hybrid fact tables.

Revision ID: 20260423_add_ontology_rules_and_facts
Revises: 20260423_add_ontology_step_metadata
Create Date: 2026-04-23 19:10:00.000000
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

try:
    from sqlite_portable import alter_column_drop_server_default, drop_column
except ModuleNotFoundError:  # pragma: no cover - import path differs in some test loaders
    from apps.backend.alembic.sqlite_portable import alter_column_drop_server_default, drop_column


revision: str = "20260423_add_ontology_rules_and_facts"
down_revision: str | Sequence[str] | None = "20260423_add_ontology_step_metadata"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _add_json_list_column(table: str, column: str) -> None:
    op.add_column(
        table,
        sa.Column(column, sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
    )
    alter_column_drop_server_default(
        table,
        column,
        coltype=sa.JSON(),
        existing_nullable=False,
        existing_server_default=sa.text("'[]'"),
    )


def upgrade() -> None:
    _add_json_list_column("ontology_candidate_entities", "query_rules")
    _add_json_list_column("ontology_candidate_entities", "facts")
    _add_json_list_column("ontology_candidate_relations", "query_rules")
    _add_json_list_column("ontology_candidate_relations", "facts")
    _add_json_list_column("ontology_entities", "query_rules")
    _add_json_list_column("ontology_relations", "query_rules")
    _add_json_list_column("ontology_entity_type_definitions", "query_rules")
    _add_json_list_column("ontology_relation_type_definitions", "query_rules")

    op.create_table(
        "ontology_entity_facts",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("workspace_id", sa.String(length=64), nullable=False),
        sa.Column("version_id", sa.String(length=64), nullable=False),
        sa.Column("entity_id", sa.String(length=64), nullable=False),
        sa.Column("metric_key", sa.String(length=128), nullable=False),
        sa.Column("value_num", sa.Float(), nullable=True),
        sa.Column("value_text", sa.Text(), nullable=True),
        sa.Column("value_bool", sa.Boolean(), nullable=True),
        sa.Column("unit", sa.String(length=64), nullable=True),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("source_document_id", sa.String(length=64), nullable=True),
        sa.Column("source_chunk_id", sa.String(length=64), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    alter_column_drop_server_default(
        "ontology_entity_facts",
        "metadata_json",
        coltype=sa.JSON(),
        existing_nullable=False,
        existing_server_default=sa.text("'{}'"),
    )
    op.create_index(op.f("ix_ontology_entity_facts_workspace_id"), "ontology_entity_facts", ["workspace_id"], unique=False)
    op.create_index(op.f("ix_ontology_entity_facts_version_id"), "ontology_entity_facts", ["version_id"], unique=False)
    op.create_index(op.f("ix_ontology_entity_facts_entity_id"), "ontology_entity_facts", ["entity_id"], unique=False)
    op.create_index(op.f("ix_ontology_entity_facts_metric_key"), "ontology_entity_facts", ["metric_key"], unique=False)
    op.create_index(op.f("ix_ontology_entity_facts_observed_at"), "ontology_entity_facts", ["observed_at"], unique=False)
    op.create_index(op.f("ix_ontology_entity_facts_source_document_id"), "ontology_entity_facts", ["source_document_id"], unique=False)
    op.create_index(op.f("ix_ontology_entity_facts_source_chunk_id"), "ontology_entity_facts", ["source_chunk_id"], unique=False)

    op.create_table(
        "ontology_relation_facts",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("workspace_id", sa.String(length=64), nullable=False),
        sa.Column("version_id", sa.String(length=64), nullable=False),
        sa.Column("relation_id", sa.String(length=64), nullable=False),
        sa.Column("metric_key", sa.String(length=128), nullable=False),
        sa.Column("value_num", sa.Float(), nullable=True),
        sa.Column("value_text", sa.Text(), nullable=True),
        sa.Column("value_bool", sa.Boolean(), nullable=True),
        sa.Column("unit", sa.String(length=64), nullable=True),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("source_document_id", sa.String(length=64), nullable=True),
        sa.Column("source_chunk_id", sa.String(length=64), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    alter_column_drop_server_default(
        "ontology_relation_facts",
        "metadata_json",
        coltype=sa.JSON(),
        existing_nullable=False,
        existing_server_default=sa.text("'{}'"),
    )
    op.create_index(op.f("ix_ontology_relation_facts_workspace_id"), "ontology_relation_facts", ["workspace_id"], unique=False)
    op.create_index(op.f("ix_ontology_relation_facts_version_id"), "ontology_relation_facts", ["version_id"], unique=False)
    op.create_index(op.f("ix_ontology_relation_facts_relation_id"), "ontology_relation_facts", ["relation_id"], unique=False)
    op.create_index(op.f("ix_ontology_relation_facts_metric_key"), "ontology_relation_facts", ["metric_key"], unique=False)
    op.create_index(op.f("ix_ontology_relation_facts_observed_at"), "ontology_relation_facts", ["observed_at"], unique=False)
    op.create_index(op.f("ix_ontology_relation_facts_source_document_id"), "ontology_relation_facts", ["source_document_id"], unique=False)
    op.create_index(op.f("ix_ontology_relation_facts_source_chunk_id"), "ontology_relation_facts", ["source_chunk_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_ontology_relation_facts_source_chunk_id"), table_name="ontology_relation_facts")
    op.drop_index(op.f("ix_ontology_relation_facts_source_document_id"), table_name="ontology_relation_facts")
    op.drop_index(op.f("ix_ontology_relation_facts_observed_at"), table_name="ontology_relation_facts")
    op.drop_index(op.f("ix_ontology_relation_facts_metric_key"), table_name="ontology_relation_facts")
    op.drop_index(op.f("ix_ontology_relation_facts_relation_id"), table_name="ontology_relation_facts")
    op.drop_index(op.f("ix_ontology_relation_facts_version_id"), table_name="ontology_relation_facts")
    op.drop_index(op.f("ix_ontology_relation_facts_workspace_id"), table_name="ontology_relation_facts")
    op.drop_table("ontology_relation_facts")

    op.drop_index(op.f("ix_ontology_entity_facts_source_chunk_id"), table_name="ontology_entity_facts")
    op.drop_index(op.f("ix_ontology_entity_facts_source_document_id"), table_name="ontology_entity_facts")
    op.drop_index(op.f("ix_ontology_entity_facts_observed_at"), table_name="ontology_entity_facts")
    op.drop_index(op.f("ix_ontology_entity_facts_metric_key"), table_name="ontology_entity_facts")
    op.drop_index(op.f("ix_ontology_entity_facts_entity_id"), table_name="ontology_entity_facts")
    op.drop_index(op.f("ix_ontology_entity_facts_version_id"), table_name="ontology_entity_facts")
    op.drop_index(op.f("ix_ontology_entity_facts_workspace_id"), table_name="ontology_entity_facts")
    op.drop_table("ontology_entity_facts")

    drop_column("ontology_relation_type_definitions", "query_rules")
    drop_column("ontology_entity_type_definitions", "query_rules")
    drop_column("ontology_relations", "query_rules")
    drop_column("ontology_entities", "query_rules")
    drop_column("ontology_candidate_relations", "facts")
    drop_column("ontology_candidate_relations", "query_rules")
    drop_column("ontology_candidate_entities", "facts")
    drop_column("ontology_candidate_entities", "query_rules")
