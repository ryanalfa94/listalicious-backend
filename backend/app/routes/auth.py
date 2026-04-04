from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, BackgroundTasks, HTTPException, status, Depends, Request
from fastapi.security import OAuth2PasswordRequestForm, HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, ConfigDict
from bson import ObjectId

from app.schemas.user import UserCreate, UserUpdate, ChangePasswordRequest, ChangeEmailRequest
from app.schemas.auth import AuthResponse
from app.services.auth_service import register_user, login_user, get_current_user, get_password_hash, verify_password
from app.database.database import get_database
from app.core.limiter import limiter
from app.services.jwt_service import verify_token, create_access_token, create_refresh_token, verify_refresh_token
from app.services.mailer import send_email_change_verification

import secrets
from hashlib import sha256

bearer = HTTPBearer()

router = APIRouter(prefix="/auth", tags=["Auth"])

EMAIL_CHANGE_TTL_MIN = 60 * 24
EMAIL_CHANGE_COOLDOWN_SEC = 60


async def _record_session(db, access_token: str, user_id: str) -> None:
    """Store a session record so users can list and revoke individual sessions."""
    payload = verify_token(access_token)
    if not payload:
        return
    try:
        await db["sessions"].insert_one({
            "jti": payload["jti"],
            "user_id": user_id,
            "created_at": datetime.utcnow(),
            "expires_at": datetime.fromtimestamp(payload["exp"]),
        })
    except Exception:
        pass  # duplicate jti on retry — safe to ignore


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
async def register(request: Request, user: UserCreate, db=Depends(get_database)):
    result = await register_user(user)
    await _record_session(db, result["access_token"], result["user"]["_id"])
    return result


@router.post("/login", response_model=AuthResponse)
@limiter.limit("10/minute")
async def login(request: Request, form_data: OAuth2PasswordRequestForm = Depends(), db=Depends(get_database)):
    result = await login_user(form_data.username, form_data.password)
    if not result:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    await _record_session(db, result["access_token"], result["user"]["_id"])
    return result


class RefreshRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    refresh_token: str


@router.post("/refresh")
@limiter.limit("60/minute")
async def refresh_tokens(request: Request, body: RefreshRequest, db=Depends(get_database)):
    """
    Exchange a valid refresh token for a new access + refresh token pair.
    The old refresh token remains valid until it expires (stateless rotation).
    token_version mismatch (from logout-all or password change) immediately rejects it.
    """
    payload = verify_refresh_token(body.refresh_token)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired refresh token")

    user_id = payload.get("sub")
    token_tv = int(payload.get("tv", 0))

    try:
        user = await db["users"].find_one({"_id": ObjectId(user_id)})
    except Exception:
        user = None
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    if int(user.get("token_version", 0)) != token_tv:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token no longer valid")

    tv = int(user.get("token_version", 0))
    new_access = create_access_token(subject=user_id, token_version=tv, extra={"email": user["email"]})
    new_refresh = create_refresh_token(subject=user_id, token_version=tv)
    await _record_session(db, new_access, user_id)
    return {"access_token": new_access, "refresh_token": new_refresh, "token_type": "bearer"}


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


@router.post("/change-password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(
    body: ChangePasswordRequest,
    db=Depends(get_database),
    user=Depends(get_current_user),
):
    if not verify_password(body.current_password, user["hashed_password"]):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Current password is incorrect")
    new_hash = get_password_hash(body.new_password)
    await db["users"].update_one(
        {"_id": user["_id"]},
        {"$set": {"hashed_password": new_hash, "updated_at": datetime.now(timezone.utc)},
         "$inc": {"token_version": 1}},
    )
    return


@router.post("/change-email", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("3/minute")
async def change_email(
    request: Request,
    body: ChangeEmailRequest,
    bg: BackgroundTasks,
    db=Depends(get_database),
    user=Depends(get_current_user),
):
    """
    Initiates an email change. Sends a verification link to the new address.
    The change is not applied until the link is clicked (POST /auth/confirm-email-change).
    """
    if not verify_password(body.password, user["hashed_password"]):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Password is incorrect")

    new_email = str(body.new_email).lower()
    if new_email == user["email"].lower():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="New email must differ from current email")

    # Check not already taken
    existing = await db["users"].find_one({"email": new_email}, {"_id": 1})
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already in use")

    user_id = str(user["_id"])
    now = datetime.utcnow()

    # Cooldown
    recent = await db["email_changes"].find_one({
        "user_id": user_id,
        "used_at": None,
        "created_at": {"$gte": now - timedelta(seconds=EMAIL_CHANGE_COOLDOWN_SEC)},
    })
    if recent:
        return

    # Invalidate previous pending change
    await db["email_changes"].update_many(
        {"user_id": user_id, "used_at": None},
        {"$set": {"used_at": now}},
    )

    raw = secrets.token_urlsafe(32)
    token_hash = sha256(raw.encode()).hexdigest()

    await db["email_changes"].insert_one({
        "user_id": user_id,
        "new_email": new_email,
        "token_hash": token_hash,
        "created_at": now,
        "expires_at": now + timedelta(minutes=EMAIL_CHANGE_TTL_MIN),
        "used_at": None,
    })

    bg.add_task(send_email_change_verification, new_email, raw)
    return


@router.get("/sessions")
async def list_sessions(db=Depends(get_database), user=Depends(get_current_user)):
    """Return all active (non-expired, non-revoked) sessions for the current user."""
    now = datetime.utcnow()
    sessions = await db["sessions"].find(
        {"user_id": str(user["_id"]), "expires_at": {"$gt": now}},
        {"_id": 0, "jti": 1, "created_at": 1, "expires_at": 1},
    ).to_list(length=100)

    revoked = set(await db["revoked_tokens"].distinct("jti", {"user_id": str(user["_id"])}))
    return [s for s in sessions if s["jti"] not in revoked]


@router.delete("/sessions/{jti}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_session(jti: str, db=Depends(get_database), user=Depends(get_current_user)):
    """Revoke a specific session by JTI. Use this to remotely log out a single device."""
    session = await db["sessions"].find_one({"jti": jti, "user_id": str(user["_id"])})
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    await db["revoked_tokens"].update_one(
        {"jti": jti},
        {"$set": {
            "jti": jti,
            "user_id": str(user["_id"]),
            "expires_at": session["expires_at"],
            "created_at": datetime.now(timezone.utc),
        }},
        upsert=True,
    )
    return


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
