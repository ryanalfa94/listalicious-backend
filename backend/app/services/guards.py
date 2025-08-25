# reusable check that (a) the list exists and (b) the current user is allowed to touch it.

from bson import ObjectId
from fastapi import HTTPException, status

async def ensure_list_access(db, list_id: str, user_id: str) -> dict:
    """
    Allow if user is owner OR in shared_with.
    404 if list not found, 403 otherwise.
    """
    try:
        oid = ObjectId(list_id)
    except Exception:
        raise HTTPException(status_code=404, detail="List not found")

    lst = await db["grocery_lists"].find_one({"_id": oid})
    if not lst:
        raise HTTPException(status_code=404, detail="List not found")

    owner_ok = str(lst.get("owner_id")) == str(user_id)
    shared_ok = str(user_id) in [str(u) for u in lst.get("shared_with", [])]

    if not (owner_ok or shared_ok):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    return lst

async def ensure_list_owned(db, list_id: str, user_id: str) -> dict:
    # keep this for owner-only ops (like sharing, deleting the list, etc.)
    lst = await ensure_list_access(db, list_id, user_id)
    if str(lst.get("owner_id")) != str(user_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Owner required")
    return lst
