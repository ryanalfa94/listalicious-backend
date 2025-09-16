
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import OAuth2PasswordRequestForm
from app.schemas.user import UserCreate
from app.schemas.auth import AuthResponse
from app.services.auth_service import register_user, login_user, get_current_user
from fastapi import Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.database.database import get_database
from backend.app.services.jwt_service import verify_token


# Create a reusable security dependency
bearer = HTTPBearer()

router = APIRouter(prefix="/auth", tags=["Auth"])

@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(user: UserCreate):
    # register_user returns {"user": {...}, "access_token": "...", "token_type": "bearer"}
    return await register_user(user)

@router.post("/login", response_model=AuthResponse)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    result = await login_user(form_data.username, form_data.password)
    if not result:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    return result

@router.get("/me")
async def read_current_user(current_user: dict = Depends(get_current_user)):
    return {
        "email": current_user["email"],
        "username": current_user.get("username"),
        "_id": str(current_user["_id"]),
        "created_at": current_user.get("created_at"),
        "updated_at": current_user.get("updated_at"),
    }

@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout_current_device(
    creds: HTTPAuthorizationCredentials = Depends(bearer),
    user = Depends(get_current_user),
    db = Depends(get_database),   # ✅ keep it here
):
    payload = verify_token(creds.credentials)
    if not payload:
        return

    jti = payload.get("jti")
    exp_ts = payload.get("exp")
    if not jti or not exp_ts:
        return

    await db["revoked_tokens"].update_one(
        {"jti": jti},
        {"$set": {
            "jti": jti,
            "user_id": str(user["_id"]),
            "expires_at": datetime.fromtimestamp(exp_ts, tz=timezone.utc),
            "created_at": datetime.now(timezone.utc),
        }},
        upsert=True
    )
    return


@router.post("/logout-all", status_code=status.HTTP_204_NO_CONTENT)
async def logout_all_devices(
    user = Depends(get_current_user),
    db = Depends(get_database),   # ✅ also here
):
    await db["users"].update_one(
        {"_id": user["_id"]},
        {"$inc": {"token_version": 1}}
    )
    return