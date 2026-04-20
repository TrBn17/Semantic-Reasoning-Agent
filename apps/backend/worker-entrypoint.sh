#!/bin/sh
set -e

echo "Running migrations before worker startup..."
python apps/backend/run_migrations.py

echo "Starting Celery worker..."
python apps/backend/worker/serve.py
