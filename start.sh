#!/bin/bash
# Railway startup script
# Runs database migrations before starting the server

set -e

# Add current directory to Python path so imports work
export PYTHONPATH=/app:$PYTHONPATH

echo "Running database migrations..."
alembic upgrade head

echo "Starting FastAPI server..."
exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
