#!/bin/bash

# Activate virtual environment
source venv/bin/activate

# Add backend/ to PYTHONPATH so Python treats it as a module root
export PYTHONPATH="$PYTHONPATH:$(pwd)/backend"

# Run the FastAPI app from the root directory
uvicorn app.main:app --reload --reload-dir backend/app
