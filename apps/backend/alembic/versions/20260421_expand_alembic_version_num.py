"""Expand alembic_version.version_num to 64 chars

Revision ID: 20260421_expand_alembic_ver
Revises: 20260421_agent_tools_onto
Create Date: 2026-04-21 00:30:00.000000
"""

from alembic import op
import sqlalchemy as sa

revision = "20260421_expand_alembic_ver"
down_revision = "20260421_agent_tools_onto"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "alembic_version",
        "version_num",
        existing_type=sa.String(length=32),
        type_=sa.String(length=64),
        existing_nullable=False,
    )


def downgrade() -> None:
    op.alter_column(
        "alembic_version",
        "version_num",
        existing_type=sa.String(length=64),
        type_=sa.String(length=32),
        existing_nullable=False,
    )
