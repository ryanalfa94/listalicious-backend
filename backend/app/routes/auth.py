from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, status, Depends, Request
from fastapi.security import OAuth2PasswordRequestForm, HTTPAuthorizationCredentials, HTTPBearer
from bson import ObjectId

from app.schemas.user import UserCreate, UserUpdate
from app.schemas.auth import AuthResponse
from app.services.auth_service import register_user, login_user, get_current_user
from app.database.database import get_database
from app.core.limiter import limiter
from app.services.jwt_service import verify_token


bearer = HTTPBearer()

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
async def register(request: Request, user: UserCreate):
    return await register_user(user)


@router.post("/login", response_model=AuthResponse)
@limiter.limit("10/minute")
async def login(request: Request, form_data: OAuth2PasswordRequestForm = Depends()):
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
        "email_verified": current_user.get("email_verified", False),
    }


@router.patch("/me", status_code=status.HTTP_200_OK)
async def update_me(
    body: UserUpdate,
    db=Depends(get_database),
    current_user: dict = Depends(get_current_user),
):
    updates = body.model_dump(exclude_unset=True)
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")
    updates["updated_at"] = datetime.now(timezone.utc)
    await db["users"].update_one({"_id": current_user["_id"]}, {"$set": updates})
    updated = await db["users"].find_one({"_id": current_user["_id"]})
    return {
        "_id": str(updated["_id"]),
        "email": updated["email"],
        "username": updated.get("username"),
        "email_verified": updated.get("email_verified", False),
        "created_at": updated.get("created_at"),
        "updated_at": updated.get("updated_at"),
    }


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout_current_device(
    creds: HTTPAuthorizationCredentials = Depends(bearer),
    user=Depends(get_current_user),
    db=Depends(get_database),
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
        upsert=True,
    )
    return


@router.post("/logout-all", status_code=status.HTTP_204_NO_CONTENT)
async def logout_all_devices(
    user=Depends(get_current_user),
    db=Depends(get_database),
):
    await db["users"].update_one(
        {"_id": user["_id"]},
        {"$inc": {"token_version": 1}},
    )
    return
