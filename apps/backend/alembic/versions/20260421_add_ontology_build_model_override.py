"""Add ontology build model override columns.

Revision ID: 20260421_ont_build_model_ovr
Revises: 20260421_doc_ingest_opts
Create Date: 2026-04-21 00:30:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision = "20260421_ont_build_model_ovr"
down_revision = "20260421_doc_ingest_opts"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    existing_columns = {column["name"] for column in inspect(bind).get_columns("ontology_builds")}
    if "extraction_provider" not in existing_columns:
        op.add_column("ontology_builds", sa.Column("extraction_provider", sa.String(length=64), nullable=True))
    if "extraction_model" not in existing_columns:
        op.add_column("ontology_builds", sa.Column("extraction_model", sa.String(length=255), nullable=True))


def downgrade() -> None:
    bind = op.get_bind()
    existing_columns = {column["name"] for column in inspect(bind).get_columns("ontology_builds")}
    if "extraction_model" in existing_columns:
        op.drop_column("ontology_builds", "extraction_model")
    if "extraction_provider" in existing_columns:
        op.drop_column("ontology_builds", "extraction_provider")
