"""Add ontology titles, merge mode, and draft graph storage.

Revision ID: 20260421_ont_draft_titles
Revises: 20260421_merge_doc_ont_heads
Create Date: 2026-04-21 22:30:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision = "20260421_ont_draft_titles"
down_revision = "20260421_merge_doc_ont_heads"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    build_columns = {column["name"] for column in inspector.get_columns("ontology_builds")}
    if "ontology_title" not in build_columns:
        op.add_column("ontology_builds", sa.Column("ontology_title", sa.String(length=255), nullable=True))
    if "ontology_summary" not in build_columns:
        op.add_column("ontology_builds", sa.Column("ontology_summary", sa.Text(), nullable=True))
    if "merge_mode" not in build_columns:
        op.add_column(
            "ontology_builds",
            sa.Column("merge_mode", sa.String(length=32), nullable=False, server_default="append"),
        )

    version_columns = {column["name"] for column in inspector.get_columns("ontology_versions")}
    if "ontology_title" not in version_columns:
        op.add_column("ontology_versions", sa.Column("ontology_title", sa.String(length=255), nullable=True))
    if "ontology_summary" not in version_columns:
        op.add_column("ontology_versions", sa.Column("ontology_summary", sa.Text(), nullable=True))

    existing_tables = set(inspector.get_table_names())
    if "ontology_graph_drafts" not in existing_tables:
        op.create_table(
            "ontology_graph_drafts",
            sa.Column("workspace_id", sa.String(length=64), primary_key=True),
            sa.Column("based_on_version_id", sa.String(length=64), nullable=True),
            sa.Column("ontology_title", sa.String(length=255), nullable=True),
            sa.Column("ontology_summary", sa.Text(), nullable=True),
            sa.Column("node_patches", sa.JSON(), nullable=False),
            sa.Column("relation_patches", sa.JSON(), nullable=False),
            sa.Column("entity_type_patches", sa.JSON(), nullable=False),
            sa.Column("relation_type_patches", sa.JSON(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    existing_tables = set(inspector.get_table_names())

    if "ontology_graph_drafts" in existing_tables:
        op.drop_table("ontology_graph_drafts")

    version_columns = {column["name"] for column in inspector.get_columns("ontology_versions")}
    if "ontology_summary" in version_columns:
        op.drop_column("ontology_versions", "ontology_summary")
    if "ontology_title" in version_columns:
        op.drop_column("ontology_versions", "ontology_title")

    build_columns = {column["name"] for column in inspector.get_columns("ontology_builds")}
    if "merge_mode" in build_columns:
        op.drop_column("ontology_builds", "merge_mode")
    if "ontology_summary" in build_columns:
        op.drop_column("ontology_builds", "ontology_summary")
    if "ontology_title" in build_columns:
        op.drop_column("ontology_builds", "ontology_title")
