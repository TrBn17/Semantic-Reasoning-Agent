from __future__ import annotations

from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import inspect

from semantic_reasoning_agent.core.config import Settings, get_settings
from semantic_reasoning_agent.persistence.database import DatabaseManager
from semantic_reasoning_agent.persistence.models import Base


class AlembicService:
    def __init__(self, database_manager: DatabaseManager, settings: Settings | None = None) -> None:
        self._database_manager = database_manager
        self._settings = settings or get_settings()
        self._backend_root = Path(__file__).resolve().parents[3]
        self._alembic_ini_path = self._backend_root / "alembic.ini"
        self._script_location = self._backend_root / "alembic"

    def upgrade(self, revision: str = "head") -> None:
        config = Config(str(self._alembic_ini_path))
        config.set_main_option("script_location", str(self._script_location))
        config.set_main_option("sqlalchemy.url", self._settings.database_url)

        with self._database_manager.engine.begin() as connection:
            inspector = inspect(connection)
            has_alembic_version = inspector.has_table("alembic_version")
            has_conversations = inspector.has_table("conversations")

            if not has_alembic_version and not has_conversations:
                # Fresh database with no historical baseline tables:
                # materialize current ORM schema and align Alembic state.
                Base.metadata.create_all(connection)
                config.attributes["connection"] = connection
                command.stamp(config, revision)
                return

            config.attributes["connection"] = connection
            command.upgrade(config, revision)