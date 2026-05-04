"""builtin_agent_context: SKILLS/MEMORY overrides per workspace for built-in agents.

Revision ID: 20260429_add_builtin_agent_context
Revises: 20260428_add_ontology_graph_projections
Create Date: 2026-04-29 12:00:00.000000
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260429_add_builtin_agent_context"
down_revision: str | Sequence[str] | None = "20260428_add_ontology_graph_projections"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "builtin_agent_context",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("workspace_id", sa.String(length=64), nullable=False),
        sa.Column("agent_role", sa.String(length=32), nullable=False),
        sa.Column("skills_body", sa.Text(), nullable=True),
        sa.Column("memory_body", sa.Text(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "workspace_id",
            "agent_role",
            name="uq_builtin_agent_context_ws_role",
        ),
    )
    op.create_index(
        op.f("ix_builtin_agent_context_workspace_id"),
        "builtin_agent_context",
        ["workspace_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_builtin_agent_context_workspace_id"), table_name="builtin_agent_context")
    op.drop_table("builtin_agent_context")
