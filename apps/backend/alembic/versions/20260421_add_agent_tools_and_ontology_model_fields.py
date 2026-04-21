"""Add agent tool assignments and ontology model fields.

Revision ID: 20260421_agent_tools_onto
Revises: 20260421_doc_ingest_opts
Create Date: 2026-04-21 00:00:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision = "20260421_agent_tools_onto"
down_revision = "20260421_doc_ingest_opts"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    profile_columns = {column["name"] for column in inspector.get_columns("agent_profiles")}
    if "tool_assignments" not in profile_columns:
        op.add_column(
            "agent_profiles",
            sa.Column(
                "tool_assignments",
                sa.JSON(),
                nullable=False,
                server_default=sa.text("'[]'"),
            ),
        )
        op.alter_column("agent_profiles", "tool_assignments", server_default=None)

    build_columns = {column["name"] for column in inspector.get_columns("ontology_builds")}
    if "provider" not in build_columns:
        op.add_column("ontology_builds", sa.Column("provider", sa.String(length=64), nullable=True))
    if "model" not in build_columns:
        op.add_column("ontology_builds", sa.Column("model", sa.String(length=128), nullable=True))


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    build_columns = {column["name"] for column in inspector.get_columns("ontology_builds")}
    if "model" in build_columns:
        op.drop_column("ontology_builds", "model")
    if "provider" in build_columns:
        op.drop_column("ontology_builds", "provider")

    profile_columns = {column["name"] for column in inspector.get_columns("agent_profiles")}
    if "tool_assignments" in profile_columns:
        op.drop_column("agent_profiles", "tool_assignments")
