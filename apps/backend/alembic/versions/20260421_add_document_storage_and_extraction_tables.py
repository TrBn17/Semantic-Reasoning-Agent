"""Add document storage refs and extraction tables.

Revision ID: 20260421_doc_storage_extract
Revises: 20260421_doc_ingest_opts
Create Date: 2026-04-21 00:30:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision = "20260421_doc_storage_extract"
down_revision = "20260421_doc_ingest_opts"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    existing_columns = {column["name"] for column in inspector.get_columns("documents")}

    if "source_object_key" not in existing_columns:
        op.add_column("documents", sa.Column("source_object_key", sa.Text(), nullable=True))
    if "source_content_type" not in existing_columns:
        op.add_column("documents", sa.Column("source_content_type", sa.String(length=255), nullable=True))
    if "size_bytes" not in existing_columns:
        op.add_column("documents", sa.Column("size_bytes", sa.Integer(), nullable=True))

    if "document_artifacts" not in inspector.get_table_names():
        op.create_table(
            "document_artifacts",
            sa.Column("id", sa.String(length=64), primary_key=True),
            sa.Column("document_id", sa.String(length=64), sa.ForeignKey("documents.id", ondelete="CASCADE"), nullable=False),
            sa.Column("workspace_id", sa.String(length=64), nullable=False),
            sa.Column("artifact_type", sa.String(length=64), nullable=False),
            sa.Column("name", sa.String(length=255), nullable=False),
            sa.Column("object_key", sa.Text(), nullable=False),
            sa.Column("public_url", sa.Text(), nullable=False),
            sa.Column("content_type", sa.String(length=255), nullable=False),
            sa.Column("size_bytes", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("metadata_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        )
        op.create_index("ix_document_artifacts_document_id", "document_artifacts", ["document_id"])
        op.create_index("ix_document_artifacts_workspace_id", "document_artifacts", ["workspace_id"])
        op.create_index("ix_document_artifacts_artifact_type", "document_artifacts", ["artifact_type"])

    if "document_extraction_runs" not in inspector.get_table_names():
        op.create_table(
            "document_extraction_runs",
            sa.Column("id", sa.String(length=64), primary_key=True),
            sa.Column("document_id", sa.String(length=64), sa.ForeignKey("documents.id", ondelete="CASCADE"), nullable=False),
            sa.Column("workspace_id", sa.String(length=64), nullable=False),
            sa.Column("status", sa.String(length=32), nullable=False),
            sa.Column("schema_json", sa.JSON(), nullable=False),
            sa.Column("result_json", sa.JSON(), nullable=True),
            sa.Column("parser_version", sa.String(length=128), nullable=True),
            sa.Column("use_llm", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("error_message", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        )
        op.create_index("ix_document_extraction_runs_document_id", "document_extraction_runs", ["document_id"])
        op.create_index("ix_document_extraction_runs_workspace_id", "document_extraction_runs", ["workspace_id"])
        op.create_index("ix_document_extraction_runs_status", "document_extraction_runs", ["status"])


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    existing_columns = {column["name"] for column in inspector.get_columns("documents")}

    if "document_extraction_runs" in inspector.get_table_names():
        op.drop_index("ix_document_extraction_runs_status", table_name="document_extraction_runs")
        op.drop_index("ix_document_extraction_runs_workspace_id", table_name="document_extraction_runs")
        op.drop_index("ix_document_extraction_runs_document_id", table_name="document_extraction_runs")
        op.drop_table("document_extraction_runs")

    if "document_artifacts" in inspector.get_table_names():
        op.drop_index("ix_document_artifacts_artifact_type", table_name="document_artifacts")
        op.drop_index("ix_document_artifacts_workspace_id", table_name="document_artifacts")
        op.drop_index("ix_document_artifacts_document_id", table_name="document_artifacts")
        op.drop_table("document_artifacts")

    if "size_bytes" in existing_columns:
        op.drop_column("documents", "size_bytes")
    if "source_content_type" in existing_columns:
        op.drop_column("documents", "source_content_type")
    if "source_object_key" in existing_columns:
        op.drop_column("documents", "source_object_key")
