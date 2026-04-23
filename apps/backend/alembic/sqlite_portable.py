"""SQLite-friendly Alembic operation helpers.

SQLite's ``ALTER TABLE`` support is limited. Operations like
``op.alter_column(..., server_default=None)`` compile to
``ALTER TABLE ... ALTER COLUMN ...`` on the generic DDL path, which fails on
SQLite. Using :func:`alembic.op.batch_alter_table` lets Alembic rewrite the
table for these changes in a portable way.
"""

from __future__ import annotations

from typing import Any

from alembic import op
import sqlalchemy as sa


def is_sqlite() -> bool:
    bind = op.get_bind()
    return bind is not None and bind.dialect.name == "sqlite"


def alter_column_drop_server_default(
    table_name: str,
    column_name: str,
    *,
    coltype: sa.types.TypeEngine,
    existing_nullable: bool,
    existing_server_default: str | sa.sql.elements.TextClause | sa.schema.DefaultClause | Any | None,
) -> None:
    """Remove a column's server default in a way that works on SQLite."""
    if is_sqlite():
        with op.batch_alter_table(table_name) as batch_op:
            batch_op.alter_column(
                column_name,
                existing_type=coltype,
                type_=coltype,
                existing_nullable=existing_nullable,
                server_default=None,
                existing_server_default=existing_server_default,
            )
    else:
        op.alter_column(table_name, column_name, server_default=None)


def drop_column(table_name: str, column_name: str) -> None:
    if is_sqlite():
        with op.batch_alter_table(table_name) as batch_op:
            batch_op.drop_column(column_name)
    else:
        op.drop_column(table_name, column_name)
