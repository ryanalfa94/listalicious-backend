# routes/list.py
from fastapi import APIRouter, Depends, Query, status, HTTPException
from bson import ObjectId
from datetime import datetime, timedelta
import secrets
from hashlib import sha256
from app.database.database import get_database
from app.services.auth_service import get_current_user
from app.services.guards import ensure_list_access, ensure_list_owned, require_verified_email
from app.services import list_service
from app.services.activity import log_activity
from app.schemas.list import GroceryListCreate, GroceryListResponse, GroceryListUpdate

router = APIRouter(prefix="/lists", tags=["Lists"])

INVITE_TTL_DAYS = 7


# ── IMPORTANT: literal-path routes must come BEFORE /{list_id} routes ──────────

@router.post("/join/{token}", status_code=status.HTTP_204_NO_CONTENT)
async def join_list_via_invite(token: str, db=Depends(get_database), user=Depends(get_current_user)):
    """Accept an invite link. Adds the authenticated user as a collaborator."""
    token_hash = sha256(token.encode()).hexdigest()
    rec = await db["list_invites"].find_one({"token_hash": token_hash})

    now = datetime.utcnow()
    if not rec or rec.get("used_at") or rec.get("expires_at") < now:
        raise HTTPException(status_code=400, detail="Invalid or expired invite link")

    list_id = rec["list_id"]
    user_id = str(user["_id"])

    # Add to shared_with (idempotent)
    await db["grocery_lists"].update_one(
        {"_id": ObjectId(list_id)},
        {"$addToSet": {"shared_with": user_id}},
    )
    await db["list_invites"].update_one({"_id": rec["_id"]}, {"$set": {"used_at": now, "used_by": user_id}})
    await log_activity(db, list_id=list_id, user_id=user_id, user_email=user["email"],
                       action="joined_via_invite")
    return


# ── Standard CRUD ──────────────────────────────────────────────────────────────

@router.post("", response_model=GroceryListResponse, status_code=status.HTTP_201_CREATED)
async def create_list(list_data: GroceryListCreate, current_user: dict = Depends(require_verified_email)):
    return await list_service.create_grocery_list(
        title=list_data.title,
        owner_id=str(current_user["_id"])
    )


@router.get("", response_model=list[GroceryListResponse])
async def get_lists(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    include_archived: bool = Query(False, description="Include archived lists"),
    db=Depends(get_database),
    user=Depends(get_current_user),
):
    return await list_service.get_my_lists(db, str(user["_id"]), skip=skip, limit=limit,
                                           include_archived=include_archived)


@router.get("/{list_id}", response_model=GroceryListResponse)
async def get_single_list(list_id: str, db=Depends(get_database), user=Depends(get_current_user)):
    await ensure_list_access(db, list_id, str(user["_id"]))
    doc = await list_service.get_list(db, list_id)
    if not doc:
        raise HTTPException(status_code=404, detail="List not found")
    return doc


@router.put("/{list_id}", response_model=GroceryListResponse)
async def update_list(list_id: str, payload: GroceryListUpdate,
                      db=Depends(get_database), user=Depends(get_current_user)):
    await ensure_list_owned(db, list_id, str(user["_id"]))
    updated = await list_service.update_list(db, list_id, payload.model_dump(exclude_unset=True))
    return updated


# ── List-level actions ─────────────────────────────────────────────────────────

@router.get("/{list_id}/stats")
async def get_list_stats(list_id: str, db=Depends(get_database), user=Depends(get_current_user)):
    """Return item counts for a list."""
    await ensure_list_access(db, list_id, str(user["_id"]))
    total = await db["items"].count_documents({"list_id": list_id})
    checked = await db["items"].count_documents({"list_id": list_id, "is_checked": True})
    return {"total": total, "checked": checked, "unchecked": total - checked}


@router.get("/{list_id}/shared-users")
async def get_shared_users(list_id: str, db=Depends(get_database), user=Depends(get_current_user)):
    lst = await ensure_list_access(db, list_id, str(user["_id"]))
    shared_ids = lst.get("shared_with", [])
    if not shared_ids:
        return []
    results = []
    for uid in shared_ids:
        try:
            u = await db["users"].find_one({"_id": ObjectId(uid)}, {"email": 1, "username": 1})
            if u:
                results.append({"id": str(u["_id"]), "email": u["email"], "username": u.get("username")})
        except Exception:
            pass
    return results


@router.post("/{list_id}/invite")
async def create_invite_link(list_id: str, db=Depends(get_database), user=Depends(get_current_user)):
    """
    Generate a single-use invite link for the list (owner only).
    The link expires after 7 days.
    """
    await ensure_list_owned(db, list_id, str(user["_id"]))
    raw = secrets.token_urlsafe(32)
    token_hash = sha256(raw.encode()).hexdigest()
    now = datetime.utcnow()
    expires_at = now + timedelta(days=INVITE_TTL_DAYS)

    await db["list_invites"].insert_one({
        "list_id": list_id,
        "token_hash": token_hash,
        "created_by": str(user["_id"]),
        "created_at": now,
        "expires_at": expires_at,
        "used_at": None,
        "used_by": None,
    })
    return {"invite_token": raw, "expires_at": expires_at.isoformat()}


@router.patch("/{list_id}/archive", status_code=status.HTTP_204_NO_CONTENT)
async def archive_list(list_id: str, db=Depends(get_database), user=Depends(get_current_user)):
    """Archive a list (owner only). Archived lists are hidden from GET /lists by default."""
    await ensure_list_owned(db, list_id, str(user["_id"]))
    await db["grocery_lists"].update_one(
        {"_id": ObjectId(list_id)},
        {"$set": {"archived": True, "updated_at": datetime.utcnow()}},
    )
    return


@router.patch("/{list_id}/unarchive", status_code=status.HTTP_204_NO_CONTENT)
async def unarchive_list(list_id: str, db=Depends(get_database), user=Depends(get_current_user)):
    """Restore an archived list."""
    await ensure_list_owned(db, list_id, str(user["_id"]))
    await db["grocery_lists"].update_one(
        {"_id": ObjectId(list_id)},
        {"$set": {"archived": False, "updated_at": datetime.utcnow()}},
    )
    return


@router.post("/{list_id}/duplicate", response_model=GroceryListResponse, status_code=status.HTTP_201_CREATED)
async def duplicate_list(list_id: str, db=Depends(get_database), user=Depends(require_verified_email)):
    """Copy a list (unchecked items only). New list is owned by the requesting user."""
    await ensure_list_access(db, list_id, str(user["_id"]))
    src = await list_service.get_list(db, list_id)
    if not src:
        raise HTTPException(status_code=404, detail="List not found")

    new_list = await list_service.create_grocery_list(
        title=f"{src['title']} (copy)",
        owner_id=str(user["_id"]),
    )

    cursor = db["items"].find({"list_id": list_id, "is_checked": False}).sort("position", 1)
    items = await cursor.to_list(length=None)
    if items:
        now = datetime.utcnow()
        new_docs = [
            {
                "name": it["name"],
                "quantity": it["quantity"],
                "unit": it.get("unit"),
                "note": it.get("note"),
                "is_checked": False,
                "list_id": new_list["_id"],
                "position": idx,
                "created_at": now,
                "updated_at": now,
            }
            for idx, it in enumerate(items)
        ]
        await db["items"].insert_many(new_docs)

    return new_list


@router.get("/{list_id}/activity")
async def get_list_activity(
    list_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db=Depends(get_database),
    user=Depends(get_current_user),
):
    """Return recent activity for a list (newest first)."""
    await ensure_list_access(db, list_id, str(user["_id"]))
    cursor = (
        db["activity_logs"]
        .find({"list_id": list_id}, {"_id": 0})
        .sort("created_at", -1)
        .skip(skip)
        .limit(limit)
    )
    return await cursor.to_list(length=limit)


@router.delete("/{list_id}/leave", status_code=status.HTTP_204_NO_CONTENT)
async def leave_list(list_id: str, db=Depends(get_database), user=Depends(get_current_user)):
    """Remove yourself as a collaborator from a shared list. Owners must delete instead."""
    try:
        oid = ObjectId(list_id)
    except Exception:
        raise HTTPException(status_code=404, detail="List not found")

    lst = await db["grocery_lists"].find_one({"_id": oid}, {"owner_id": 1, "shared_with": 1})
    if not lst:
        raise HTTPException(status_code=404, detail="List not found")

    user_id = str(user["_id"])
    if str(lst.get("owner_id")) == user_id:
        raise HTTPException(status_code=400, detail="Owners cannot leave their own list. Delete it instead.")

    if user_id not in [str(u) for u in lst.get("shared_with", [])]:
        raise HTTPException(status_code=400, detail="You are not a collaborator on this list.")

    await db["grocery_lists"].update_one({"_id": oid}, {"$pull": {"shared_with": user_id}})
    await log_activity(db, list_id=list_id, user_id=user_id, user_email=user["email"],
                       action="collaborator_left")
    return


@router.delete("/{list_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_list(list_id: str, db=Depends(get_database), user=Depends(get_current_user)):
    await ensure_list_owned(db, list_id, str(user["_id"]))
    await list_service.delete_list(db, list_id)
    return
