"""add knowledge pack tables

Revision ID: 20260422_add_knowledge_pack_tables
Revises: 20260421_merge_doc_ont_heads
Create Date: 2026-04-22 00:45:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect


revision: str = "20260422_add_knowledge_pack_tables"
down_revision: str | Sequence[str] | None = "20260421_merge_doc_ont_heads"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    existing_tables = set(inspector.get_table_names())

    if "knowledge_packs" not in existing_tables:
        op.create_table(
            "knowledge_packs",
            sa.Column("id", sa.String(length=64), nullable=False),
            sa.Column("workspace_id", sa.String(length=64), nullable=False),
            sa.Column("name", sa.String(length=255), nullable=False),
            sa.Column("description", sa.Text(), nullable=False, server_default=""),
            sa.Column("status", sa.String(length=32), nullable=False, server_default="active"),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )

    knowledge_pack_indexes = {index["name"] for index in inspector.get_indexes("knowledge_packs")}
    workspace_index_name = op.f("ix_knowledge_packs_workspace_id")
    if workspace_index_name not in knowledge_pack_indexes:
        op.create_index(workspace_index_name, "knowledge_packs", ["workspace_id"], unique=False)

    status_index_name = op.f("ix_knowledge_packs_status")
    if status_index_name not in knowledge_pack_indexes:
        op.create_index(status_index_name, "knowledge_packs", ["status"], unique=False)

    if "knowledge_pack_documents" not in existing_tables:
        op.create_table(
            "knowledge_pack_documents",
            sa.Column("knowledge_pack_id", sa.String(length=64), nullable=False),
            sa.Column("document_id", sa.String(length=64), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["knowledge_pack_id"], ["knowledge_packs.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("knowledge_pack_id", "document_id"),
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    existing_tables = set(inspector.get_table_names())

    if "knowledge_pack_documents" in existing_tables:
        op.drop_table("knowledge_pack_documents")

    if "knowledge_packs" in existing_tables:
        knowledge_pack_indexes = {index["name"] for index in inspector.get_indexes("knowledge_packs")}
        status_index_name = op.f("ix_knowledge_packs_status")
        if status_index_name in knowledge_pack_indexes:
            op.drop_index(status_index_name, table_name="knowledge_packs")

        workspace_index_name = op.f("ix_knowledge_packs_workspace_id")
        if workspace_index_name in knowledge_pack_indexes:
            op.drop_index(workspace_index_name, table_name="knowledge_packs")

        op.drop_table("knowledge_packs")
