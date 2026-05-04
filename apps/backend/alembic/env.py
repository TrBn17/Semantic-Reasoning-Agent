from __future__ import annotations

import os
import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import engine_from_config, pool

BASE_DIR = Path(__file__).resolve().parents[1]
ALEMBIC_DIR = Path(__file__).resolve().parent
SRC_DIR = BASE_DIR / "src"
# Alembic loads revision scripts as plain modules; add this directory so shared
# helpers (e.g. sqlite_portable) can be imported without colliding with the
# installed `alembic` package name.
if str(ALEMBIC_DIR) not in sys.path:
    sys.path.insert(0, str(ALEMBIC_DIR))
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from semantic_reasoning_agent.core.config import get_settings
from semantic_reasoning_agent.persistence.models import Base

config = context.config

if config.config_file_name is not None:
    # Default True would disable unrelated loggers (e.g. uvicorn.access); then HTTP access lines stop.
    fileConfig(config.config_file_name, disable_existing_loggers=False)

target_metadata = Base.metadata


def get_database_url() -> str:
    return os.environ.get("DATABASE_URL", get_settings().database_url)


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url") or get_database_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connection = config.attributes.get("connection")
    if connection is not None:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )
        with context.begin_transaction():
            context.run_migrations()
        return

    configuration = config.get_section(config.config_ini_section) or {}
    configuration["sqlalchemy.url"] = configuration.get("sqlalchemy.url") or get_database_url()
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()