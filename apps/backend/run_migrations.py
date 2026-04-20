from pathlib import Path
import sys


def main() -> None:
    print("Running database migrations...")
    backend_src = Path(__file__).resolve().parent / "src"
    sys.path.insert(0, str(backend_src))

    from semantic_reasoning_agent.persistence.database import get_database_manager
    from semantic_reasoning_agent.services.alembic_service import AlembicService

    db = get_database_manager()
    db.create_schema()
    AlembicService(db).upgrade()
    print("Database migrations completed successfully")


if __name__ == "__main__":
    main()
