#!/bin/bash

# Ensure the script runs from the repo root
cd "$(dirname "$0")"

# Run the FastAPI app using the local .venv python and backend on PYTHONPATH
PYTHONPATH="$(pwd)/backend" ./.venv/Scripts/python.exe -m uvicorn app.main:app --reload --reload-dir backend/app
