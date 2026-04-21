"""Add document ingestion options.

Revision ID: 20260421_doc_ingest_opts
Revises: 20260420_ontology_type_defs
Create Date: 2026-04-21 00:00:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision = "20260421_doc_ingest_opts"
down_revision = "20260420_ontology_type_defs"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    existing_columns = {column["name"] for column in inspect(bind).get_columns("documents")}
    if "ingestion_options" not in existing_columns:
        op.add_column(
            "documents",
            sa.Column(
                "ingestion_options",
                sa.JSON(),
                nullable=False,
                server_default=sa.text("'{}'"),
            ),
        )
        op.alter_column("documents", "ingestion_options", server_default=None)


def downgrade() -> None:
    bind = op.get_bind()
    existing_columns = {column["name"] for column in inspect(bind).get_columns("documents")}
    if "ingestion_options" in existing_columns:
        op.drop_column("documents", "ingestion_options")
