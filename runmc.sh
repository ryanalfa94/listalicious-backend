#!/bin/bash
set -e

# Activate virtual environment
source venv/bin/activate

cd backend

# Add backend/ to PYTHONPATH
export PYTHONPATH="$PYTHONPATH:$(pwd)"

# Run FastAPI app
uvicorn app.main:app --reload --reload-dir app