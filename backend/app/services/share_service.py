# app/services/share_service.py
from bson import ObjectId
from fastapi import HTTPException

async def add_contributor(db, list_id: str, contributor_user_id: str) -> list[str]:
    """
    Idempotently add a user_id to shared_with via $addToSet.
    Returns the updated shared_with list (as strings).
    """
    try:
        oid = ObjectId(list_id)
    except Exception:
        raise HTTPException(status_code=404, detail="List not found")

    res = await db["grocery_lists"].update_one(
        {"_id": oid},
        {"$addToSet": {"shared_with": str(contributor_user_id)}}
    )
    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail="List not found")

    doc = await db["grocery_lists"].find_one({"_id": oid}, {"shared_with": 1})
    return [str(u) for u in (doc.get("shared_with") or [])]

async def remove_contributor(db, list_id: str, contributor_user_id: str) -> list[str]:
    """
    Remove a user_id from shared_with via $pull.
    Returns the updated shared_with list (as strings).
    """
    try:
        oid = ObjectId(list_id)
    except Exception:
        raise HTTPException(status_code=404, detail="List not found")

    await db["grocery_lists"].update_one(
        {"_id": oid},
        {"$pull": {"shared_with": str(contributor_user_id)}}
    )
    doc = await db["grocery_lists"].find_one({"_id": oid}, {"shared_with": 1})
    return [str(u) for u in (doc.get("shared_with") or [])]
