from __future__ import annotations

from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory
import pytest
from sqlalchemy import create_engine, inspect, text

from semantic_reasoning_agent.core.config import Settings
from semantic_reasoning_agent.persistence.database import DatabaseManager
from semantic_reasoning_agent.persistence.models import Base, ConversationORM
from semantic_reasoning_agent.services.alembic_service import AlembicService


HEAD_REVISION = "20260423_drop_ontology_candidate_tables"


def _sqlite_url(path: Path) -> str:
    return f"sqlite+pysqlite:///{path.as_posix()}"


def _settings_for_db(path: Path) -> Settings:
    return Settings(APP_ENV="test", DATABASE_URL=_sqlite_url(path), DATABASE_ECHO=False)


def _compare_schema_against_metadata(database_url: str) -> None:
    engine = create_engine(database_url, future=True)
    inspector = inspect(engine)

    actual_tables = set(inspector.get_table_names())
    expected_tables = set(Base.metadata.tables)
    assert actual_tables == expected_tables | {"alembic_version"}

    for table_name, table in Base.metadata.tables.items():
        actual_columns = {column["name"]: column for column in inspector.get_columns(table_name)}
        expected_columns = {column.name: column for column in table.columns}
        assert set(actual_columns) == set(expected_columns), table_name

        for column_name, expected in expected_columns.items():
            actual = actual_columns[column_name]
            actual_type = actual["type"]
            assert actual_type._compare_type_affinity(expected.type), f"{table_name}.{column_name} type"
            if getattr(expected.type, "length", None) is not None:
                assert getattr(actual_type, "length", None) == expected.type.length, f"{table_name}.{column_name} length"
            assert bool(actual["nullable"]) == expected.nullable, f"{table_name}.{column_name} nullable"
            assert bool(actual.get("primary_key")) == expected.primary_key, f"{table_name}.{column_name} pk"
            assert actual.get("default") in (None, "NULL"), f"{table_name}.{column_name} default"

        actual_fks = {
            (
                tuple(item["constrained_columns"]),
                item["referred_table"],
                tuple(item["referred_columns"]),
                (item.get("options") or {}).get("ondelete"),
            )
            for item in inspector.get_foreign_keys(table_name)
        }
        expected_fks = {
            (
                tuple(element.parent.name for element in constraint.elements),
                constraint.elements[0].column.table.name,
                tuple(element.column.name for element in constraint.elements),
                constraint.ondelete,
            )
            for constraint in table.foreign_key_constraints
        }
        assert actual_fks == expected_fks, table_name

        actual_indexes = {
            (
                item["name"],
                tuple(item["column_names"]),
                bool(item.get("unique", False)),
            )
            for item in inspector.get_indexes(table_name)
        }
        expected_indexes = {
            (
                index.name,
                tuple(column.name for column in index.columns),
                bool(index.unique),
            )
            for index in table.indexes
        }
        assert actual_indexes == expected_indexes, table_name

    engine.dispose()


def test_upgrade_uses_alembic_baseline_for_fresh_database(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    db_path = tmp_path / "fresh.db"
    settings = _settings_for_db(db_path)
    manager = DatabaseManager(settings)
    service = AlembicService(manager, settings)

    def _forbidden_create_all(*args, **kwargs):  # noqa: ANN002, ANN003
        raise AssertionError("AlembicService.upgrade() must not fall back to Base.metadata.create_all().")

    monkeypatch.setattr(Base.metadata, "create_all", _forbidden_create_all)

    service.upgrade()

    with manager.engine.connect() as connection:
        revision = connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one()
    assert revision == HEAD_REVISION

    inspector = inspect(manager.engine)
    assert set(Base.metadata.tables).issubset(set(inspector.get_table_names()))


def test_alembic_history_has_single_head() -> None:
    backend_root = Path(__file__).resolve().parents[1]
    config = Config(str(backend_root / "alembic.ini"))
    config.set_main_option("script_location", str(backend_root / "alembic"))
    script = ScriptDirectory.from_config(config)

    assert script.get_heads() == [HEAD_REVISION]


def test_upgrade_rejects_unversioned_database_with_existing_tables(tmp_path: Path) -> None:
    db_path = tmp_path / "legacy.db"
    settings = _settings_for_db(db_path)
    manager = DatabaseManager(settings)
    ConversationORM.__table__.create(manager.engine)

    with pytest.raises(RuntimeError, match="not tracked by Alembic"):
        AlembicService(manager, settings).upgrade()


def test_baseline_schema_matches_sqlalchemy_metadata(tmp_path: Path) -> None:
    db_path = tmp_path / "baseline.db"
    settings = _settings_for_db(db_path)
    manager = DatabaseManager(settings)

    AlembicService(manager, settings).upgrade()

    _compare_schema_against_metadata(settings.database_url)
