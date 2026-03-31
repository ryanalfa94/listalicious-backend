from fastapi import APIRouter, Depends, BackgroundTasks, status, HTTPException
from datetime import datetime, timedelta
from hashlib import sha256
import secrets
from bson import ObjectId

from app.database.database import get_database
from app.services.auth_service import get_current_user, get_password_hash
from app.services.mailer import send_email_verification, send_password_reset
from app.schemas.verification import (
    EmailVerificationToken,
    ForgotPasswordRequest,
    ResetPasswordRequest,
)

router = APIRouter(prefix="/auth", tags=["Auth"])

# token lifetimes
VERIFY_TTL_MIN = 60 * 24   # 24h
RESET_TTL_MIN  = 30        # 30 minutes
RESEND_COOLDOWN_SEC = 60   # minimum seconds between resend requests

# -------------------------
# Email verification
# -------------------------

@router.post("/request-email-verification", status_code=status.HTTP_204_NO_CONTENT)
async def request_email_verification(
    bg: BackgroundTasks,
    db = Depends(get_database),
    user = Depends(get_current_user),
):
    """
    Sends a one-time verification link to the authenticated user's email.
    - Idempotent: always 204 (even if already verified).
    - Enforces a 60-second cooldown to prevent spam.
    - Invalidates any previous unused tokens before issuing a new one.
    """
    if user.get("email_verified") is True:
        return

    email = user["email"]
    user_id = str(user["_id"])
    now = datetime.utcnow()

    # Cooldown: silently ignore if a token was issued in the last 60 seconds
    recent = await db["email_verifications"].find_one({
        "user_id": user_id,
        "used_at": None,
        "created_at": {"$gte": now - timedelta(seconds=RESEND_COOLDOWN_SEC)},
    })
    if recent:
        return

    # Invalidate all previous unused tokens for this user
    await db["email_verifications"].update_many(
        {"user_id": user_id, "used_at": None},
        {"$set": {"used_at": now}},
    )

    raw = secrets.token_urlsafe(32)
    token_hash = sha256(raw.encode()).hexdigest()

    await db["email_verifications"].insert_one({
        "user_id": user_id,
        "email": email,
        "token_hash": token_hash,
        "created_at": now,
        "expires_at": now + timedelta(minutes=VERIFY_TTL_MIN),
        "used_at": None,
    })

    bg.add_task(send_email_verification, email, raw)
    return


@router.post("/verify-email", status_code=status.HTTP_204_NO_CONTENT)
async def verify_email(
    body: EmailVerificationToken,
    db = Depends(get_database),
):
    """
    Accept a token and mark user.email_verified = True if valid and unexpired.
    """
    token_hash = sha256(body.token.encode()).hexdigest()
    rec = await db["email_verifications"].find_one({"token_hash": token_hash})

    now = datetime.utcnow()
    if not rec or rec.get("used_at") or rec.get("expires_at") < now:
        raise HTTPException(status_code=400, detail="Invalid or expired token")

    user_id = rec["user_id"]
    await db["users"].update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {
            "email_verified": True,
            "email_verified_at": now,
            "updated_at": now,
        }}
    )
    await db["email_verifications"].update_one({"_id": rec["_id"]}, {"$set": {"used_at": now}})
    return

# -------------------------
# Password reset (logged-out)
# -------------------------

@router.post("/forgot-password", status_code=status.HTTP_204_NO_CONTENT)
async def forgot_password(
    body: ForgotPasswordRequest,
    bg: BackgroundTasks,
    db = Depends(get_database),
):
    """
    Always returns 204 to avoid account enumeration.
    If the email exists, creates a one-time, expiring reset token and emails it.
    Enforces a 60-second cooldown and invalidates previous unused tokens.
    """
    user = await db["users"].find_one({"email": body.email}, {"_id": 1, "email": 1})
    if not user:
        return

    user_id = str(user["_id"])
    now = datetime.utcnow()

    # Cooldown: silently ignore if a token was issued in the last 60 seconds
    recent = await db["password_resets"].find_one({
        "user_id": user_id,
        "used_at": None,
        "created_at": {"$gte": now - timedelta(seconds=RESEND_COOLDOWN_SEC)},
    })
    if recent:
        return

    # Invalidate all previous unused reset tokens for this user
    await db["password_resets"].update_many(
        {"user_id": user_id, "used_at": None},
        {"$set": {"used_at": now}},
    )

    raw = secrets.token_urlsafe(32)
    token_hash = sha256(raw.encode()).hexdigest()

    await db["password_resets"].insert_one({
        "user_id": user_id,
        "token_hash": token_hash,
        "created_at": now,
        "expires_at": now + timedelta(minutes=RESET_TTL_MIN),
        "used_at": None,
    })

    bg.add_task(send_password_reset, body.email, raw)
    return


@router.post("/reset-password", status_code=status.HTTP_204_NO_CONTENT)
async def reset_password(
    body: ResetPasswordRequest,
    db = Depends(get_database),
):
    """
    Verifies one-time token, sets new password, and bumps token_version so all
    existing tokens are invalidated immediately.
    Password strength and confirmation are validated by the schema.
    """
    token_hash = sha256(body.token.encode()).hexdigest()
    rec = await db["password_resets"].find_one({"token_hash": token_hash})

    now = datetime.utcnow()
    if not rec or rec.get("used_at") or rec.get("expires_at") < now:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")

    user_id = rec["user_id"]
    new_hash = get_password_hash(body.new_password)

    await db["users"].update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {
            "hashed_password": new_hash,
            "password_changed_at": now,
            "updated_at": now,
        },
         "$inc": {"token_version": 1}}
    )
    await db["password_resets"].update_one({"_id": rec["_id"]}, {"$set": {"used_at": now}})

    return
