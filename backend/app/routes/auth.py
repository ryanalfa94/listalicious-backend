# routes/auth.py
# Handles user registration route

from fastapi import APIRouter, HTTPException, status, Depends
from app.schemas.user import UserCreate, UserResponse
from app.services.auth_service import register_user, login_user, get_current_user
from app.schemas.token import Token
from fastapi.security import OAuth2PasswordRequestForm



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


@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    token = await login_user(form_data.username, form_data.password)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )
    return {"access_token": token, "token_type": "bearer"}


@router.get("/me")
async def read_current_user(current_user: dict = Depends(get_current_user)):
    return {
        "email": current_user["email"],
        "username": current_user.get("username"),
        "_id": str(current_user["_id"]),
        "created_at": current_user.get("created_at"),
        "updated_at": current_user.get("updated_at"),
    }