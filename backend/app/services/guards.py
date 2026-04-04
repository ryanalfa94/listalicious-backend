# reusable guards for list access control and account state checks.

from bson import ObjectId
from fastapi import HTTPException, status, Depends
from app.services.auth_service import get_current_user


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


async def require_verified_email(user: dict = Depends(get_current_user)) -> dict:
    """
    Dependency that rejects requests from users who have not verified their email.
    Use on any endpoint that should be gated behind email verification.
    """
    if not user.get("email_verified"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email verification required. Please verify your email address to continue.",
        )
    return user
