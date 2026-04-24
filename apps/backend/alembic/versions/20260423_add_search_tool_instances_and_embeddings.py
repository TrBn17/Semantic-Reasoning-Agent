"""Add workspace search settings, tool-instance metadata, and embedding indexes.

Revision ID: 20260423_add_search_tool_instances_and_embeddings
Revises: 20260423_add_ontology_rules_and_facts
Create Date: 2026-04-23 23:30:00.000000
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

try:
    from sqlite_portable import alter_column_drop_server_default, is_sqlite
except ModuleNotFoundError:  # pragma: no cover - import path differs in some test loaders
    from apps.backend.alembic.sqlite_portable import (
        alter_column_drop_server_default,
        is_sqlite,
    )


revision: str = "20260423_add_search_tool_instances_and_embeddings"
down_revision: str | Sequence[str] | None = "20260423_add_ontology_rules_and_facts"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _has_table(table_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return table_name in inspector.get_table_names()


def _has_column(table_name: str, column_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return any(column["name"] == column_name for column in inspector.get_columns(table_name))


def _has_unique_constraint(table_name: str, constraint_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return any(
        constraint["name"] == constraint_name
        for constraint in inspector.get_unique_constraints(table_name)
    )


def _has_index(table_name: str, index_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return any(index["name"] == index_name for index in inspector.get_indexes(table_name))


def _ensure_search_tool_configs_table() -> None:
    if _has_table("search_tool_configs"):
        return
    op.create_table(
        "search_tool_configs",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("workspace_id", sa.String(length=64), nullable=False),
        sa.Column("tool_type", sa.String(length=16), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("provider", sa.String(length=64), nullable=False),
        sa.Column("model", sa.String(length=128), nullable=False),
        sa.Column("default_top_k", sa.Integer(), nullable=False),
        sa.Column("collection_target", sa.String(length=64), nullable=False),
        sa.Column("document_ids", sa.JSON(), nullable=False),
        sa.Column("bm25_enabled", sa.Boolean(), nullable=False),
        sa.Column("fusion_strategy", sa.String(length=32), nullable=False),
        sa.Column("ontology_scope", sa.String(length=32), nullable=False),
        sa.Column("ontology_version_id", sa.String(length=64), nullable=True),
        sa.Column("graph_search_type", sa.String(length=16), nullable=False),
        sa.Column("reranker", sa.String(length=32), nullable=False),
        sa.Column("config_metadata", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "workspace_id",
            "tool_type",
            "name",
            name="uq_search_tool_configs_name",
        ),
    )
    op.create_index(
        op.f("ix_search_tool_configs_workspace_id"),
        "search_tool_configs",
        ["workspace_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_search_tool_configs_tool_type"),
        "search_tool_configs",
        ["tool_type"],
        unique=False,
    )


def upgrade() -> None:
    op.create_table(
        "workspace_search_settings",
        sa.Column("workspace_id", sa.String(length=64), nullable=False),
        sa.Column("embedding_provider", sa.String(length=64), nullable=False),
        sa.Column("embedding_model", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("workspace_id"),
    )

    _ensure_search_tool_configs_table()

    if not _has_column("search_tool_configs", "system_key"):
        op.add_column(
            "search_tool_configs",
            sa.Column("system_key", sa.String(length=128), nullable=True),
        )
    if not _has_column("search_tool_configs", "is_system"):
        op.add_column(
            "search_tool_configs",
            sa.Column("is_system", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        )
        alter_column_drop_server_default(
            "search_tool_configs",
            "is_system",
            coltype=sa.Boolean(),
            existing_nullable=False,
            existing_server_default=sa.text("false"),
        )
    if not _has_column("search_tool_configs", "embedding_provider"):
        op.add_column(
            "search_tool_configs",
            sa.Column("embedding_provider", sa.String(length=64), nullable=False, server_default="cloudflare"),
        )
        alter_column_drop_server_default(
            "search_tool_configs",
            "embedding_provider",
            coltype=sa.String(length=64),
            existing_nullable=False,
            existing_server_default=sa.text("'cloudflare'"),
        )
    if not _has_column("search_tool_configs", "embedding_model"):
        op.add_column(
            "search_tool_configs",
            sa.Column("embedding_model", sa.String(length=255), nullable=False, server_default=""),
        )
        alter_column_drop_server_default(
            "search_tool_configs",
            "embedding_model",
            coltype=sa.String(length=255),
            existing_nullable=False,
            existing_server_default=sa.text("''"),
        )
    op.execute(
        "UPDATE search_tool_configs "
        "SET embedding_provider = COALESCE(NULLIF(provider, ''), 'cloudflare'), "
        "embedding_model = COALESCE(model, '')"
    )
    if not is_sqlite() and not _has_unique_constraint("search_tool_configs", "uq_search_tool_configs_system_key"):
        op.create_unique_constraint(
            "uq_search_tool_configs_system_key",
            "search_tool_configs",
            ["workspace_id", "system_key"],
        )

    op.add_column(
        "document_chunks",
        sa.Column("embedding_provider", sa.String(length=64), nullable=True),
    )
    op.add_column(
        "document_chunks",
        sa.Column("embedding_model", sa.String(length=255), nullable=True),
    )

    op.create_table(
        "ontology_search_index",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("workspace_id", sa.String(length=64), nullable=False),
        sa.Column("version_id", sa.String(length=64), nullable=False),
        sa.Column("item_type", sa.String(length=32), nullable=False),
        sa.Column("item_id", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("embedding", sa.JSON(), nullable=False),
        sa.Column("embedding_provider", sa.String(length=64), nullable=False),
        sa.Column("embedding_model", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_ontology_search_index_workspace_id"),
        "ontology_search_index",
        ["workspace_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_ontology_search_index_version_id"),
        "ontology_search_index",
        ["version_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_ontology_search_index_item_type"),
        "ontology_search_index",
        ["item_type"],
        unique=False,
    )
    op.create_index(
        op.f("ix_ontology_search_index_item_id"),
        "ontology_search_index",
        ["item_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_ontology_search_index_item_id"), table_name="ontology_search_index")
    op.drop_index(op.f("ix_ontology_search_index_item_type"), table_name="ontology_search_index")
    op.drop_index(op.f("ix_ontology_search_index_version_id"), table_name="ontology_search_index")
    op.drop_index(op.f("ix_ontology_search_index_workspace_id"), table_name="ontology_search_index")
    op.drop_table("ontology_search_index")

    op.drop_column("document_chunks", "embedding_model")
    op.drop_column("document_chunks", "embedding_provider")

    if _has_table("search_tool_configs"):
        if _has_unique_constraint("search_tool_configs", "uq_search_tool_configs_system_key"):
            op.drop_constraint("uq_search_tool_configs_system_key", "search_tool_configs", type_="unique")
        if _has_column("search_tool_configs", "embedding_model"):
            op.drop_column("search_tool_configs", "embedding_model")
        if _has_column("search_tool_configs", "embedding_provider"):
            op.drop_column("search_tool_configs", "embedding_provider")
        if _has_column("search_tool_configs", "is_system"):
            op.drop_column("search_tool_configs", "is_system")
        if _has_column("search_tool_configs", "system_key"):
            op.drop_column("search_tool_configs", "system_key")

    op.drop_table("workspace_search_settings")
