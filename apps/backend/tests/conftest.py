import os
import sys
from pathlib import Path

import pytest

os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")
os.environ.setdefault("DATABASE_ECHO", "false")
os.environ.setdefault("CELERY_BROKER_URL", "memory://")
os.environ.setdefault("CELERY_RESULT_BACKEND", "cache+memory://")
os.environ.setdefault("CELERY_TASK_ALWAYS_EAGER", "true")
os.environ.setdefault("CELERY_TASK_EAGER_PROPAGATES", "true")
os.environ.setdefault("NEO4J_ENABLED", "false")


BACKEND_SRC = Path(__file__).resolve().parents[1] / "src"
if str(BACKEND_SRC) not in sys.path:
    sys.path.insert(0, str(BACKEND_SRC))

from semantic_reasoning_agent.entrypoints.dependencies import (  # noqa: E402
    get_document_service,
    get_ontology_service,
)
from semantic_reasoning_agent.core.container import get_app_container  # noqa: E402


@pytest.fixture(autouse=True)
def reset_database() -> None:
    get_app_container().database_manager.reset_schema()


@pytest.fixture
def document_service():
    return get_document_service()


@pytest.fixture
def ontology_service():
    return get_ontology_service()
