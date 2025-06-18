# backend/app/main.py

from fastapi import FastAPI
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

# Register all routers
app.include_router(auth.router)
