"""Add ontology type definition tables.

Revision ID: 20260420_ontology_type_defs
Revises: 20260418_init_conv_ws
Create Date: 2026-04-20 00:00:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision = "20260420_ontology_type_defs"
down_revision = "20260418_init_conv_ws"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    existing_tables = set(inspector.get_table_names())

    if "ontology_entity_type_definitions" not in existing_tables:
        op.create_table(
            "ontology_entity_type_definitions",
            sa.Column("id", sa.String(length=64), primary_key=True),
            sa.Column(
                "version_id",
                sa.String(length=64),
                sa.ForeignKey("ontology_versions.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column("workspace_id", sa.String(length=64), nullable=False),
            sa.Column("name", sa.String(length=128), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("attributes", sa.JSON(), nullable=False),
            sa.Column("examples", sa.JSON(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        )
        op.create_index(
            "ix_ontology_entity_type_definitions_version_id",
            "ontology_entity_type_definitions",
            ["version_id"],
        )
        op.create_index(
            "ix_ontology_entity_type_definitions_workspace_id",
            "ontology_entity_type_definitions",
            ["workspace_id"],
        )
        op.create_index(
            "ix_ontology_entity_type_definitions_name",
            "ontology_entity_type_definitions",
            ["name"],
        )

    if "ontology_relation_type_definitions" not in existing_tables:
        op.create_table(
            "ontology_relation_type_definitions",
            sa.Column("id", sa.String(length=64), primary_key=True),
            sa.Column(
                "version_id",
                sa.String(length=64),
                sa.ForeignKey("ontology_versions.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column("workspace_id", sa.String(length=64), nullable=False),
            sa.Column("name", sa.String(length=128), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("attributes", sa.JSON(), nullable=False),
            sa.Column("allowed_source_targets", sa.JSON(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        )
        op.create_index(
            "ix_ontology_relation_type_definitions_version_id",
            "ontology_relation_type_definitions",
            ["version_id"],
        )
        op.create_index(
            "ix_ontology_relation_type_definitions_workspace_id",
            "ontology_relation_type_definitions",
            ["workspace_id"],
        )
        op.create_index(
            "ix_ontology_relation_type_definitions_name",
            "ontology_relation_type_definitions",
            ["name"],
        )


def downgrade() -> None:
    bind = op.get_bind()
    existing_tables = set(inspect(bind).get_table_names())

    if "ontology_relation_type_definitions" in existing_tables:
        op.drop_index(
            "ix_ontology_relation_type_definitions_name",
            table_name="ontology_relation_type_definitions",
        )
        op.drop_index(
            "ix_ontology_relation_type_definitions_workspace_id",
            table_name="ontology_relation_type_definitions",
        )
        op.drop_index(
            "ix_ontology_relation_type_definitions_version_id",
            table_name="ontology_relation_type_definitions",
        )
        op.drop_table("ontology_relation_type_definitions")

    if "ontology_entity_type_definitions" in existing_tables:
        op.drop_index(
            "ix_ontology_entity_type_definitions_name",
            table_name="ontology_entity_type_definitions",
        )
        op.drop_index(
            "ix_ontology_entity_type_definitions_workspace_id",
            table_name="ontology_entity_type_definitions",
        )
        op.drop_index(
            "ix_ontology_entity_type_definitions_version_id",
            table_name="ontology_entity_type_definitions",
        )
        op.drop_table("ontology_entity_type_definitions")
