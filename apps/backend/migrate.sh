#!/bin/sh
set -e

echo "Running database migrations..."
cd /workspace
export PYTHONPATH="/workspace/apps/backend/src:$PYTHONPATH"
python -c "
from semantic_reasoning_agent.persistence.database import get_database_manager
from semantic_reasoning_agent.services.alembic_service import AlembicService

db = get_database_manager()
db.create_schema()
AlembicService(db).upgrade()
print('Database migrations completed successfully')
"
