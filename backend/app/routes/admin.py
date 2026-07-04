from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict
from bson import ObjectId

from app.database.database import get_database
from app.services.auth_service import get_current_user

router = APIRouter(prefix="/admin", tags=["Admin"])


class AdminUserStatusUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    is_active: bool


async def _require_admin(user: dict) -> dict:
    if user.get("role") != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return user


@router.get("/users")
async def list_users(db=Depends(get_database), user=Depends(get_current_user)):
    await _require_admin(user)
    cursor = db["users"].find({}, {"hashed_password": 0}).sort("created_at", -1).limit(100)
    docs = await cursor.to_list(length=100)
    return [
        {
            "_id": str(u["_id"]),
            "email": u["email"],
            "username": u.get("username"),
            "email_verified": u.get("email_verified", False),
            "role": u.get("role", "user"),
            "is_active": u.get("is_active", True),
            "created_at": u.get("created_at"),
            "updated_at": u.get("updated_at"),
        }
        for u in docs
    ]


@router.patch("/users/{user_id}/status", status_code=status.HTTP_200_OK)
async def update_user_status(
    user_id: str,
    body: AdminUserStatusUpdate,
    db=Depends(get_database),
    user=Depends(get_current_user),
):
    await _require_admin(user)

    try:
        target_id = ObjectId(user_id)
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Invalid user id") from exc

    updated = await db["users"].find_one_and_update(
        {"_id": target_id},
        {"$set": {"is_active": body.is_active, "updated_at": datetime.now(timezone.utc)}},
        return_document=True,
    )
    if not updated:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "_id": str(updated["_id"]),
        "email": updated["email"],
        "is_active": updated.get("is_active", True),
        "role": updated.get("role", "user"),
    }
