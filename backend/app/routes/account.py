# app/routes/account.py
from fastapi import APIRouter, Depends, status, HTTPException
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from bson import ObjectId
from datetime import datetime, timezone
import re

from app.database.database import get_database
from app.services.auth_service import (
    get_current_user,
    verify_password,     # <- must match your auth_service names
    get_password_hash,   # <- must match your auth_service names
)

router = APIRouter(prefix="/auth", tags=["Account"])

# -------------------------------------------------------------------
# Models
# -------------------------------------------------------------------

class ChangePassword(BaseModel):
    """
    Client provides the current password and the desired new password.
    We also accept an optional confirmation field for DX (reject if mismatch).
    """
    model_config = ConfigDict(extra="forbid")

    current_password: str = Field(min_length=1)
    new_password: str = Field(min_length=8)
    confirm_new_password: Optional[str] = None


# -------------------------------------------------------------------
# Utilities
# -------------------------------------------------------------------

def _validate_new_password_rules(new_pw: str) -> None:
    """
    Minimal but reasonable rules for V1. Adjust as you see fit:
    - ≥ 8 chars
    - at least one letter
    - at least one digit
    """
    if len(new_pw) < 8:
        raise HTTPException(status_code=422, detail="New password must be at least 8 characters long.")
    if not re.search(r"[A-Za-z]", new_pw):
        raise HTTPException(status_code=422, detail="New password must contain at least one letter.")
    if not re.search(r"\d", new_pw):
        raise HTTPException(status_code=422, detail="New password must contain at least one digit.")


# -------------------------------------------------------------------
# Routes
# -------------------------------------------------------------------

@router.post("/change-password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(
    body: ChangePassword,
    db = Depends(get_database),
    user = Depends(get_current_user),
):
    """
    Verify current password, validate & set new password, and immediately
    invalidate all existing tokens by bumping token_version.
    Returns 204 No Content.
    """
    user_id = str(user["_id"])

    # 1) confirm body.confirm_new_password if provided
    if body.confirm_new_password is not None and body.new_password != body.confirm_new_password:
        raise HTTPException(status_code=422, detail="New password and confirmation do not match.")

    # 2) verify current password
    hashed = user.get("hashed_password")
    if not hashed or not verify_password(body.current_password, hashed):
        # Same error to avoid oracle: do not reveal which part failed
        raise HTTPException(status_code=400, detail="Current password is incorrect.")

    # 3) basic new password rules
    _validate_new_password_rules(body.new_password)

    # 4) disallow reusing the same password
    if verify_password(body.new_password, hashed):
        raise HTTPException(status_code=400, detail="New password must be different from the current password.")

    # 5) hash and save + bump token_version (logs out everywhere)
    new_hash = get_password_hash(body.new_password)
    await db["users"].update_one(
        {"_id": ObjectId(user_id)},
        {
            "$set": {
                "hashed_password": new_hash,
                "password_changed_at": datetime.now(timezone.utc),
            },
            "$inc": {"token_version": 1},
        },
    )

    # 204 — no body
    return


@router.delete("/delete-account", status_code=status.HTTP_204_NO_CONTENT)
async def delete_account(
    db = Depends(get_database),
    user = Depends(get_current_user),
):
    """
    Hard-delete the user and all of their data:
      - revoke tokens (token_version++)
      - delete items for lists they own
      - delete lists they own
      - remove them from other lists' shared_with
      - delete the user doc
    """
    user_id = str(user["_id"])

    # 1) revoke tokens now
    await db["users"].update_one({"_id": ObjectId(user_id)}, {"$inc": {"token_version": 1}})

    # 2) cascade delete: list -> items -> list docs
    cursor = db["grocery_lists"].find({"owner_id": user_id}, {"_id": 1})
    owned_list_ids = [str(doc["_id"]) async for doc in cursor]

    if owned_list_ids:
        await db["items"].delete_many({"list_id": {"$in": owned_list_ids}})
    await db["grocery_lists"].delete_many({"owner_id": user_id})

    # 3) remove from other lists' shared_with
    await db["grocery_lists"].update_many(
        {"shared_with": user_id},
        {"$pull": {"shared_with": user_id}}
    )

    # 4) delete user record
    await db["users"].delete_one({"_id": ObjectId(user_id)})

    return
