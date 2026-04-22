"""add knowledge pack tables

Revision ID: 20260422_add_knowledge_pack_tables
Revises: 20260421_merge_doc_storage_and_ontology_override_heads
Create Date: 2026-04-22 00:45:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "20260422_add_knowledge_pack_tables"
down_revision: str | Sequence[str] | None = "20260421_merge_doc_storage_and_ontology_override_heads"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
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
    op.create_index(op.f("ix_knowledge_packs_workspace_id"), "knowledge_packs", ["workspace_id"], unique=False)
    op.create_index(op.f("ix_knowledge_packs_status"), "knowledge_packs", ["status"], unique=False)

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
    op.drop_table("knowledge_pack_documents")
    op.drop_index(op.f("ix_knowledge_packs_status"), table_name="knowledge_packs")
    op.drop_index(op.f("ix_knowledge_packs_workspace_id"), table_name="knowledge_packs")
    op.drop_table("knowledge_packs")
