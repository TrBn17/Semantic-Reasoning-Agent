"""Add ingestion_mode to documents.

Revision ID: 20260423_add_document_ingestion_mode
Revises: 20260422_baseline
Create Date: 2026-04-23 09:30:00.000000
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

try:
    from sqlite_portable import alter_column_drop_server_default, drop_column, is_sqlite
except ModuleNotFoundError:  # pragma: no cover - import path differs in some test loaders
    from apps.backend.alembic.sqlite_portable import (
        alter_column_drop_server_default,
        drop_column,
        is_sqlite,
    )


revision: str = "20260423_add_document_ingestion_mode"
down_revision: str | Sequence[str] | None = "20260422_baseline"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    _alter_alembic_version_string_length(64)
    op.add_column(
        "documents",
        sa.Column("ingestion_mode", sa.String(length=32), nullable=False, server_default="both"),
    )
    op.execute("UPDATE documents SET ingestion_mode = 'both' WHERE ingestion_mode IS NULL")
    alter_column_drop_server_default(
        "documents",
        "ingestion_mode",
        coltype=sa.String(length=32),
        existing_nullable=False,
        existing_server_default=sa.text("'both'"),
    )
    op.create_index(op.f("ix_documents_ingestion_mode"), "documents", ["ingestion_mode"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_documents_ingestion_mode"), table_name="documents")
    drop_column("documents", "ingestion_mode")
    _alter_alembic_version_string_length(32)


def _alter_alembic_version_string_length(new_length: int) -> None:
    """Widen (or narrow) `alembic_version.version_num` in a DB-portable way.

    SQLite does not support ``ALTER TABLE ... ALTER COLUMN``; Alembic's
    :func:`op.batch_alter_table` rewrites the table in batch mode, which
    makes this migration work for SQLite as well as Postgres.
    """
    if is_sqlite():
        with op.batch_alter_table("alembic_version") as batch_op:
            batch_op.alter_column(
                "version_num",
                existing_type=sa.String(length=32 if new_length == 64 else 64),
                type_=sa.String(length=new_length),
                existing_nullable=False,
            )
    else:
        op.alter_column(
            "alembic_version",
            "version_num",
            existing_type=sa.String(length=32 if new_length == 64 else 64),
            type_=sa.String(length=new_length),
            existing_nullable=False,
        )
