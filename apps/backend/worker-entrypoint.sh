#!/bin/sh
set -e

echo "Running migrations before worker startup..."
sh apps/backend/migrate.sh

echo "Starting Celery worker..."
python apps/backend/worker/serve.py
