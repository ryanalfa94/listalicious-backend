# routes/users.py
from fastapi import APIRouter, Depends, Query, Request, HTTPException
from bson import ObjectId
from app.database.database import get_database
from app.services.auth_service import get_current_user
from app.core.limiter import limiter

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/search")
@limiter.limit("30/minute")
async def search_users(
    request: Request,
    q: str = Query(min_length=1, max_length=100, description="Search term matched against email and username"),
    db=Depends(get_database),
    user=Depends(get_current_user),
):
    """
    Find users by email or username prefix (case-insensitive).
    Returns up to 20 results, excluding the requesting user.
    Intended for the sharing flow — find who to share a list with.
    """
    regex = {"$regex": q, "$options": "i"}
    cursor = db["users"].find(
        {"$or": [{"email": regex}, {"username": regex}], "_id": {"$ne": user["_id"]}},
        {"email": 1, "username": 1},
    ).limit(20)
    docs = await cursor.to_list(length=20)
    return [{"id": str(u["_id"]), "email": u["email"], "username": u.get("username")} for u in docs]


@router.get("/{user_id}")
async def get_user_by_id(
    user_id: str,
    db=Depends(get_database),
    user=Depends(get_current_user),
):
    """
    Resolve a user's public identity by id. Used to show a list owner's
    name/email on the Share screen — GET /lists/{id} only returns owner_id.
    """
    try:
        oid = ObjectId(user_id)
    except Exception:
        raise HTTPException(status_code=404, detail="User not found")

    target = await db["users"].find_one({"_id": oid}, {"email": 1, "username": 1})
    if not target:
        raise HTTPException(status_code=404, detail="User not found")

    return {"id": str(target["_id"]), "email": target["email"], "username": target.get("username")}
