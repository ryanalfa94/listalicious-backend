#!/bin/bash
set -e

# Activate virtual environment
source backend/venv/bin/activate

# Add backend/ to PYTHONPATH
export PYTHONPATH="$PYTHONPATH:$(pwd)/backend"

# Run FastAPI app
uvicorn app.main:app --reload --reload-dir backend/app