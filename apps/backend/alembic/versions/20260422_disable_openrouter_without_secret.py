"""disable auto-enabled openrouter configs without saved API key.

Revision ID: 20260422_dis_openrouter
Revises: 20260422_merge_all_heads
Create Date: 2026-04-22 18:20:00.000000
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect


revision: str = "20260422_dis_openrouter"
down_revision: str | Sequence[str] | None = "20260422_merge_all_heads"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    existing_tables = set(inspector.get_table_names())
    if "provider_configs" not in existing_tables or "provider_secrets" not in existing_tables:
        return

    provider_configs = sa.table(
        "provider_configs",
        sa.column("id", sa.String),
        sa.column("workspace_id", sa.String),
        sa.column("provider", sa.String),
        sa.column("enabled", sa.Boolean),
        sa.column("env_values", sa.JSON),
    )
    provider_secrets = sa.table(
        "provider_secrets",
        sa.column("workspace_id", sa.String),
        sa.column("provider", sa.String),
        sa.column("field_key", sa.String),
        sa.column("secret_value", sa.Text),
    )

    rows = bind.execute(
        sa.select(
            provider_configs.c.id,
            provider_configs.c.workspace_id,
            provider_configs.c.provider,
            provider_configs.c.env_values,
        ).where(
            provider_configs.c.provider == "openrouter",
            provider_configs.c.enabled.is_(True),
        )
    ).fetchall()

    for row in rows:
        env_values = row.env_values or {}
        has_non_secret_values = bool(env_values)
        has_secret = bind.execute(
            sa.select(sa.literal(1)).where(
                provider_secrets.c.workspace_id == row.workspace_id,
                provider_secrets.c.provider == row.provider,
                provider_secrets.c.field_key == "OPENROUTER_API_KEY",
                provider_secrets.c.secret_value.is_not(None),
                provider_secrets.c.secret_value != "",
            )
        ).first()
        if has_non_secret_values or has_secret:
            continue
        bind.execute(
            provider_configs.update()
            .where(provider_configs.c.id == row.id)
            .values(enabled=False)
        )


def downgrade() -> None:
    # Data migration is intentionally not reversed.
    pass

