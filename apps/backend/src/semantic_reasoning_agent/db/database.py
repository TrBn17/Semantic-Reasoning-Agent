from contextlib import contextmanager
from functools import lru_cache
from typing import Iterator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from semantic_reasoning_agent.config import Settings, get_settings
from semantic_reasoning_agent.db.models import Base


class DatabaseManager:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self.engine = self._build_engine(settings)
        self._session_factory = sessionmaker(
            bind=self.engine,
            autoflush=False,
            expire_on_commit=False,
        )

    @staticmethod
    def _build_engine(settings: Settings) -> Engine:
        engine_kwargs: dict[str, object] = {
            "echo": settings.database_echo,
            "future": True,
        }
        if settings.database_url.startswith("sqlite"):
            engine_kwargs["connect_args"] = {"check_same_thread": False}
            if ":memory:" in settings.database_url:
                engine_kwargs["poolclass"] = StaticPool
        return create_engine(settings.database_url, **engine_kwargs)

    @contextmanager
    def session(self) -> Iterator[Session]:
        session = self._session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def create_schema(self) -> None:
        Base.metadata.create_all(self.engine)

    def drop_schema(self) -> None:
        Base.metadata.drop_all(self.engine)

    def reset_schema(self) -> None:
        self.drop_schema()
        self.create_schema()


@lru_cache
def get_database_manager() -> DatabaseManager:
    return DatabaseManager(get_settings())
