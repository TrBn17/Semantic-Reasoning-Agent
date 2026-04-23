"""Add metadata_json to ontology build steps.

Revision ID: 20260423_add_ontology_step_metadata
Revises: 20260423_add_document_ingestion_mode
Create Date: 2026-04-23 14:30:00.000000
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

try:
    from sqlite_portable import alter_column_drop_server_default, drop_column
except ModuleNotFoundError:  # pragma: no cover - import path differs in some test loaders
    from apps.backend.alembic.sqlite_portable import alter_column_drop_server_default, drop_column


revision: str = "20260423_add_ontology_step_metadata"
down_revision: str | Sequence[str] | None = "20260423_add_document_ingestion_mode"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "ontology_build_steps",
        sa.Column("metadata_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
    )
    alter_column_drop_server_default(
        "ontology_build_steps",
        "metadata_json",
        coltype=sa.JSON(),
        existing_nullable=False,
        existing_server_default=sa.text("'{}'"),
    )


def downgrade() -> None:
    drop_column("ontology_build_steps", "metadata_json")
