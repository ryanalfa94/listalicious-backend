from fastapi import APIRouter, Depends, BackgroundTasks, Request, status, HTTPException
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import secrets
from bson import ObjectId

from app.database.database import get_database
from app.services.auth_service import get_current_user, get_password_hash
from app.services.mailer import send_email_verification, send_password_reset
from app.core.limiter import limiter
from app.schemas.verification import (
    EmailVerificationToken,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    ConfirmEmailChangeRequest,
)

router = APIRouter(prefix="/auth", tags=["Auth"])


def _normalize_datetime(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


# token lifetimes
VERIFY_TTL_MIN = 60 * 24   # 24h
RESET_TTL_MIN  = 30        # 30 minutes
RESEND_COOLDOWN_SEC = 60


# -------------------------
# Email verification
# -------------------------

@router.post("/request-email-verification", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("3/minute")
async def request_email_verification(
    request: Request,
    bg: BackgroundTasks,
    db=Depends(get_database),
    user=Depends(get_current_user),
):
    if user.get("email_verified") is True:
        return

    email = user["email"]
    user_id = str(user["_id"])
    now = datetime.now(timezone.utc)

    recent = await db["email_verifications"].find_one({
        "user_id": user_id,
        "used_at": None,
        "created_at": {"$gte": now - timedelta(seconds=RESEND_COOLDOWN_SEC)},
    })
    if recent:
        return

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
@limiter.limit("10/minute")
async def verify_email(
    request: Request,
    body: EmailVerificationToken,
    db=Depends(get_database),
):
    token_hash = sha256(body.token.encode()).hexdigest()
    rec = await db["email_verifications"].find_one({"token_hash": token_hash})

    now = datetime.now(timezone.utc)
    expires_at = _normalize_datetime(rec.get("expires_at")) if rec else None
    if not rec or rec.get("used_at") or expires_at is None or expires_at < now:
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
# Email change confirmation
# -------------------------

@router.post("/confirm-email-change", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("10/minute")
async def confirm_email_change(
    request: Request,
    body: ConfirmEmailChangeRequest,
    db=Depends(get_database),
):
    """
    Verifies the one-time token sent to the new email address, then
    applies the email change and bumps token_version to invalidate all sessions.
    """
    token_hash = sha256(body.token.encode()).hexdigest()
    rec = await db["email_changes"].find_one({"token_hash": token_hash})

    now = datetime.now(timezone.utc)
    expires_at = _normalize_datetime(rec.get("expires_at")) if rec else None
    if not rec or rec.get("used_at") or expires_at is None or expires_at < now:
        raise HTTPException(status_code=400, detail="Invalid or expired token")

    user_id = rec["user_id"]
    new_email = rec["new_email"]

    # Final check: new email not grabbed by someone else in the meantime
    conflict = await db["users"].find_one({"email": new_email, "_id": {"$ne": ObjectId(user_id)}})
    if conflict:
        raise HTTPException(status_code=409, detail="Email already in use")

    await db["users"].update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"email": new_email, "email_verified": True, "updated_at": now},
         "$inc": {"token_version": 1}},
    )
    await db["email_changes"].update_one({"_id": rec["_id"]}, {"$set": {"used_at": now}})
    return


# -------------------------
# Password reset (logged-out)
# -------------------------

@router.post("/forgot-password", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("3/minute")
async def forgot_password(
    request: Request,
    body: ForgotPasswordRequest,
    bg: BackgroundTasks,
    db=Depends(get_database),
):
    user = await db["users"].find_one({"email": body.email}, {"_id": 1, "email": 1})
    if not user:
        return

    user_id = str(user["_id"])
    now = datetime.now(timezone.utc)

    recent = await db["password_resets"].find_one({
        "user_id": user_id,
        "used_at": None,
        "created_at": {"$gte": now - timedelta(seconds=RESEND_COOLDOWN_SEC)},
    })
    if recent:
        return

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
@limiter.limit("10/minute")
async def reset_password(
    request: Request,
    body: ResetPasswordRequest,
    db=Depends(get_database),
):
    token_hash = sha256(body.token.encode()).hexdigest()
    rec = await db["password_resets"].find_one({"token_hash": token_hash})

    now = datetime.now(timezone.utc)
    expires_at = _normalize_datetime(rec.get("expires_at")) if rec else None
    if not rec or rec.get("used_at") or expires_at is None or expires_at < now:
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
