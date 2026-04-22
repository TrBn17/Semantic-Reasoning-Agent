"""Merge document storage/extraction and ontology model override heads.

Revision ID: 20260421_merge_doc_ont_heads
Revises: 20260421_doc_storage_extract, 20260421_ont_build_model_ovr
Create Date: 2026-04-21 01:40:00.000000
"""

from __future__ import annotations


revision = "20260421_merge_doc_ont_heads"
down_revision = (
    "20260421_doc_storage_extract",
    "20260421_ont_build_model_ovr",
)
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
