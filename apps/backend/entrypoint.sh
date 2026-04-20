#!/bin/sh
set -e

echo "Running migrations before API startup..."
python apps/backend/run_migrations.py

echo "Starting API server..."
python apps/backend/serve.py
