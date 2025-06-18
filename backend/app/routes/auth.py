# routes/auth.py
# Handles user registration route

from fastapi import APIRouter, HTTPException, status
from app.schemas.user import UserCreate, UserResponse
from app.services.auth_service import register_user


router = APIRouter(
    prefix="/auth",
    tags=["Auth"]
)

@router.post("/register", response_model=UserResponse)
async def register(user: UserCreate):
    """
    Handles user registration.
    - Checks if user email already exists
    - Hashes password
    - Saves new user to MongoDB
    - Returns UserResponse (without password)
    """
    return await register_user(user)