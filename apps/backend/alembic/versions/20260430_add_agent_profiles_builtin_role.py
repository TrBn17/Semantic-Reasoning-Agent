"""agent_profiles.builtin_agent_role: sync built-in orchestrator/graph/docs profiles per workspace.

Revision ID: 20260430_add_agent_profiles_builtin_role
Revises: 20260429_add_builtin_agent_context
Create Date: 2026-04-30 12:00:00.000000
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260430_add_agent_profiles_builtin_role"
down_revision: str | Sequence[str] | None = "20260429_add_builtin_agent_context"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "agent_profiles",
        sa.Column("builtin_agent_role", sa.String(length=32), nullable=True),
    )
    op.create_index(
        "ix_agent_profiles_builtin_agent_role",
        "agent_profiles",
        ["builtin_agent_role"],
        unique=False,
    )
    op.create_unique_constraint(
        "uq_agent_profiles_workspace_builtin_role",
        "agent_profiles",
        ["workspace_id", "builtin_agent_role"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_agent_profiles_workspace_builtin_role", "agent_profiles", type_="unique")
    op.drop_index("ix_agent_profiles_builtin_agent_role", table_name="agent_profiles")
    op.drop_column("agent_profiles", "builtin_agent_role")
