"""ontology_graph_projections: scoped Graphiti partitions per knowledge pack.

Revision ID: 20260428_add_ontology_graph_projections
Revises: 20260423_drop_ontology_candidate_tables
Create Date: 2026-04-28 12:00:00.000000
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260428_add_ontology_graph_projections"
down_revision: str | Sequence[str] | None = "20260423_drop_ontology_candidate_tables"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "ontology_graph_projections",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("workspace_id", sa.String(length=64), nullable=False),
        sa.Column("knowledge_pack_id", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["knowledge_pack_id"],
            ["knowledge_packs.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "workspace_id",
            "knowledge_pack_id",
            "name",
            name="uq_ontology_graph_projections_ws_pack_name",
        ),
    )
    op.create_index(
        op.f("ix_ontology_graph_projections_workspace_id"),
        "ontology_graph_projections",
        ["workspace_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_ontology_graph_projections_knowledge_pack_id"),
        "ontology_graph_projections",
        ["knowledge_pack_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_ontology_graph_projections_knowledge_pack_id"), table_name="ontology_graph_projections")
    op.drop_index(op.f("ix_ontology_graph_projections_workspace_id"), table_name="ontology_graph_projections")
    op.drop_table("ontology_graph_projections")
