# reusable check that (a) the list exists and (b) the current user is allowed to touch it.

from bson import ObjectId
from fastapi import HTTPException, status

async def ensure_list_owned(db, list_id: str, user_id: str) -> dict:
    """
    - 404 if invalid id or list not found
    - 403 if the list exists but belongs to someone else
    - returns the list document if allowed
    """
    try:
        oid = ObjectId(list_id)
    except Exception:
        raise HTTPException(status_code=404, detail="List not found")

    lst = await db["grocery_lists"].find_one({"_id": oid})
    if not lst:
        raise HTTPException(status_code=404, detail="List not found")

    # owner check (later you can expand here to support shared_with, roles, etc.)
    if str(lst.get("owner_id")) != str(user_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    return lst
