# backend/app/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.schemas.user import UserCreate
from app.routes import auth
from app.routes import list as list_routes
from app.routes import item as item_routes
from app.routes import share as share_routes


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
app.include_router(list_routes.router, tags=["Grocery Lists"])
app.include_router(item_routes.router)
app.include_router(share_routes.router)
