#!/bin/bash

# Activate virtual environment
source venv/bin/activate

# Navigate to the backend app folder
cd backend/app

# Run the FastAPI server with auto-reload
uvicorn main:app --reload
