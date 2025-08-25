# backend/app/main.py

from fastapi import FastAPI
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

# Register all routers
app.include_router(auth.router)
app.include_router(list_routes.router, tags=["Grocery Lists"])
app.include_router(item_routes.router)
app.include_router(share_routes.router)
