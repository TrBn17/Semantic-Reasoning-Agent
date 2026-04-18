"""Init conversation workspace columns.

Revision ID: 20260418_init_conv_ws
Revises: 
Create Date: 2026-04-18 00:00:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision = "20260418_init_conv_ws"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    existing_columns = {column["name"] for column in inspect(bind).get_columns("conversations")}

    if "workspace_id" not in existing_columns:
        op.add_column(
            "conversations",
            sa.Column(
                "workspace_id",
                sa.String(length=64),
                nullable=True,
                server_default=sa.text("'workspace-demo'"),
            ),
        )
        op.execute(
            sa.text("UPDATE conversations SET workspace_id = 'workspace-demo' WHERE workspace_id IS NULL")
        )
        op.alter_column(
            "conversations",
            "workspace_id",
            existing_type=sa.String(length=64),
            nullable=False,
            server_default=None,
        )

    if "agent_profile_id" not in existing_columns:
        op.add_column(
            "conversations",
            sa.Column("agent_profile_id", sa.String(length=64), nullable=True),
        )

    if "uses_model_override" not in existing_columns:
        op.add_column(
            "conversations",
            sa.Column(
                "uses_model_override",
                sa.Boolean(),
                nullable=False,
                server_default=sa.false(),
            ),
        )


def downgrade() -> None:
    bind = op.get_bind()
    existing_columns = {column["name"] for column in inspect(bind).get_columns("conversations")}

    if "uses_model_override" in existing_columns:
        op.drop_column("conversations", "uses_model_override")

    if "agent_profile_id" in existing_columns:
        op.drop_column("conversations", "agent_profile_id")

    if "workspace_id" in existing_columns:
        op.drop_column("conversations", "workspace_id")