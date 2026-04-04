# services/auth_service.py
# Business logic for user registration

from fastapi import HTTPException, status, Depends
from app.schemas.user import UserCreate, UserResponse
from app.models.user import User
from app.database.database import user_collection
from passlib.context import CryptContext
from bson import ObjectId
from passlib.context import CryptContext
from app.database.database import get_user_by_email
from app.services.jwt_service import create_access_token, create_refresh_token, verify_token
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer


from datetime import datetime, timedelta, timezone
from typing import Optional

MAX_FAILED_LOGINS = 10      # attempts before lockout
LOCKOUT_MINUTES   = 15      # how long the lockout lasts

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
bearer_scheme = HTTPBearer()

# Pre-computed at startup — used to keep login timing consistent whether or
# not the email exists (prevents user-enumeration via timing).
_DUMMY_HASH = pwd_context.hash("__dummy__")

# ---------- Register (auto-login) ----------
async def register_user(user_data) -> dict:
    # 1) unique email
    existing_user = await user_collection.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    # 2) hash password
    hashed_password = pwd_context.hash(user_data.password)
    now = datetime.utcnow()

    # 3) insert with token_version
    user_doc = {
        "email": user_data.email,
        "username": user_data.username,
        "hashed_password": hashed_password,
        "created_at": now,
        "updated_at": now,
        "token_version": 0,
        "email_verified": False,
    }

    res = await user_collection.insert_one(user_doc)
    user_id = str(res.inserted_id)

    # 4) create tokens
    token = create_access_token(subject=user_id, token_version=0, extra={"email": user_data.email})
    refresh = create_refresh_token(subject=user_id, token_version=0)

    # 5) build response
    user_out = {
        "_id": user_id,
        "email": user_data.email,
        "username": user_data.username,
        "created_at": now,
        "updated_at": now,
        "email_verified": False,
    }
    return {"user": user_out, "access_token": token, "refresh_token": refresh, "token_type": "bearer"}

# ---------- Login (same response shape) ----------
async def login_user(email: str, password: str) -> Optional[dict]:
    user = await get_user_by_email(email)
    if not user:
        # Constant-time path: run a real bcrypt verify (always False) so that
        # login timing is the same whether the email exists or not.
        pwd_context.verify(password, _DUMMY_HASH)
        return None

    now = datetime.utcnow()

    # Check lockout
    locked_until = user.get("locked_until")
    if locked_until and locked_until > now:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Account temporarily locked due to too many failed login attempts. Try again later.",
        )

    # Verify password
    if not pwd_context.verify(password, user["hashed_password"]):
        new_count = user.get("failed_login_count", 0) + 1
        update: dict = {"failed_login_count": new_count}
        if new_count >= MAX_FAILED_LOGINS:
            update["locked_until"] = now + timedelta(minutes=LOCKOUT_MINUTES)
        await user_collection.update_one({"_id": user["_id"]}, {"$set": update})
        return None

    # Success — reset lockout state
    await user_collection.update_one(
        {"_id": user["_id"]},
        {"$set": {"failed_login_count": 0, "locked_until": None}},
    )

    tv = int(user.get("token_version", 0))
    token = create_access_token(subject=str(user["_id"]), token_version=tv, extra={"email": user["email"]})
    refresh = create_refresh_token(subject=str(user["_id"]), token_version=tv)

    user_out = {
        "_id": str(user["_id"]),
        "email": user["email"],
        "username": user.get("username"),
        "created_at": user.get("created_at"),
        "updated_at": user.get("updated_at"),
        "email_verified": user.get("email_verified", False),
    }
    return {"user": user_out, "access_token": token, "refresh_token": refresh, "token_type": "bearer"}

# ---------- Current user with token_version enforcement ----------
async def get_current_user(token: HTTPAuthorizationCredentials = Depends(bearer_scheme)):
    payload = verify_token(token.credentials)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

    user_id = payload.get("sub")
    token_tv = int(payload.get("tv", 0))
    jti = payload.get("jti")  # <--- read jti
    exp_ts = payload.get("exp")

    if not user_id or not jti or not exp_ts:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    # 1) check revocation (single-device logout)
    # If present, this token is logged out even if still valid.
    revoked = await user_collection.database["revoked_tokens"].find_one({"jti": jti})
    if revoked:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token revoked")

    # 2) load user & compare token_version
    try:
        user = await user_collection.find_one({"_id": ObjectId(user_id)})
    except Exception:
        user = None
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    if int(user.get("token_version", 0)) != token_tv:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token no longer valid")

    return user





def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def get_password_hash(plain: str) -> str:
    return pwd_context.hash(plain)