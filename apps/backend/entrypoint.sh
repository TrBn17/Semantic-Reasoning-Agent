#!/bin/sh
set -e

echo "Running migrations before API startup..."
sh apps/backend/migrate.sh

echo "Starting API server..."
python apps/backend/serve.py
