# backend/app/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.schemas.user import UserCreate
from app.routes import auth


app = FastAPI(
    title="Listalicious API",
    version="1.0.0",
    description="Backend for the Listalicious grocery list app."
)

@app.get("/")
async def read_root():
    return {"message": "Listalicious backend is alive!"}

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8081", "https://localhost:8081"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Register all routers
app.include_router(auth.router)
