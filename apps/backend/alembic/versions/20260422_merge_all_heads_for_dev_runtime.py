"""merge all current alembic heads for runtime/dev

Revision ID: 20260422_merge_all_heads
Revises: 20260421_ont_draft_titles, 20260421_expand_alembic_ver, 20260422_add_task_runtime_audit_tables
Create Date: 2026-04-22 10:55:00.000000
"""

from __future__ import annotations

from collections.abc import Sequence


revision: str = "20260422_merge_all_heads"
down_revision: str | Sequence[str] | None = (
    "20260421_ont_draft_titles",
    "20260421_expand_alembic_ver",
    "20260422_add_task_runtime_audit_tables",
)
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Merge-only revision: no DDL change.
    pass


def downgrade() -> None:
    # Merge-only revision: no DDL change.
    pass
