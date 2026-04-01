# routes/item.py
from fastapi import APIRouter, HTTPException, Query, status, Depends
from typing import Optional
from pydantic import BaseModel, ConfigDict
from app.database.database import get_database
from app.services.auth_service import get_current_user
from app.services.guards import ensure_list_access, require_verified_email
from app.services.activity import log_activity
from app.schemas.item import ItemCreate, ItemBulkCreate, ItemUpdate, ItemReorderRequest, ItemResponse
from pymongo import UpdateOne
from bson import ObjectId
from datetime import datetime

router = APIRouter(prefix="/lists/{list_id}/items", tags=["Items"])


@router.get("", response_model=list[ItemResponse])
async def list_items(
    list_id: str,
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(50, ge=1, le=200, description="Max items to return"),
    checked: Optional[bool] = Query(None, description="Filter by checked status. Omit to return all items."),
    db=Depends(get_database),
    user=Depends(get_current_user),
):
    await ensure_list_access(db, list_id, str(user["_id"]))
    item_filter: dict = {"list_id": list_id}
    if checked is not None:
        item_filter["is_checked"] = checked
    cursor = (
        db["items"]
        .find(item_filter)
        .sort([("position", 1), ("created_at", 1)])
        .skip(skip)
        .limit(limit)
    )
    docs = await cursor.to_list(length=limit)
    for d in docs:
        d["_id"] = str(d["_id"])
    return [ItemResponse(**d) for d in docs]


@router.post("", response_model=ItemResponse, status_code=status.HTTP_201_CREATED)
async def create_item(list_id: str, item: ItemCreate, db=Depends(get_database), user=Depends(require_verified_email)):
    await ensure_list_access(db, list_id, str(user["_id"]))
    now = datetime.utcnow()
    position = await db["items"].count_documents({"list_id": list_id})
    doc = {
        "name": item.name,
        "quantity": item.quantity,
        "unit": item.unit,
        "note": item.note,
        "is_checked": item.is_checked or False,
        "list_id": list_id,
        "position": position,
        "created_at": now,
        "updated_at": now,
    }
    res = await db["items"].insert_one(doc)
    doc["_id"] = str(res.inserted_id)
    await log_activity(db, list_id=list_id, user_id=str(user["_id"]), user_email=user["email"],
                       action="item_added", meta={"item_id": doc["_id"], "item_name": item.name})
    return ItemResponse(**doc)


@router.post("/bulk", response_model=list[ItemResponse], status_code=status.HTTP_201_CREATED)
async def bulk_create_items(
    list_id: str,
    body: ItemBulkCreate,
    db=Depends(get_database),
    user=Depends(require_verified_email),
):
    """Add up to 50 items in a single request."""
    await ensure_list_access(db, list_id, str(user["_id"]))
    now = datetime.utcnow()
    base_position = await db["items"].count_documents({"list_id": list_id})
    docs = [
        {
            "name": it.name,
            "quantity": it.quantity,
            "unit": it.unit,
            "note": it.note,
            "is_checked": it.is_checked or False,
            "list_id": list_id,
            "position": base_position + idx,
            "created_at": now,
            "updated_at": now,
        }
        for idx, it in enumerate(body.items)
    ]
    result = await db["items"].insert_many(docs)
    for doc, oid in zip(docs, result.inserted_ids):
        doc["_id"] = str(oid)
    await log_activity(db, list_id=list_id, user_id=str(user["_id"]), user_email=user["email"],
                       action="items_bulk_added", meta={"count": len(docs)})
    return [ItemResponse(**d) for d in docs]


@router.patch("/reorder", status_code=status.HTTP_204_NO_CONTENT)
async def reorder_items(
    list_id: str,
    body: ItemReorderRequest,
    db=Depends(get_database),
    user=Depends(get_current_user),
):
    """
    Set display order for items. Send an ordered list of item IDs;
    each item's position becomes its index in the array.
    Items not included keep their current position.
    """
    await ensure_list_access(db, list_id, str(user["_id"]))
    ops = [
        UpdateOne(
            {"_id": ObjectId(item_id), "list_id": list_id},
            {"$set": {"position": idx, "updated_at": datetime.utcnow()}},
        )
        for idx, item_id in enumerate(body.order)
    ]
    if ops:
        await db["items"].bulk_write(ops, ordered=False)
    return


@router.patch("/{item_id}/check", response_model=ItemResponse)
async def toggle_item_check(list_id: str, item_id: str, db=Depends(get_database), user=Depends(get_current_user)):
    await ensure_list_access(db, list_id, str(user["_id"]))
    doc = await db["items"].find_one({"_id": ObjectId(item_id), "list_id": list_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Item not found")
    now = datetime.utcnow()
    new_checked = not doc.get("is_checked", False)
    await db["items"].update_one(
        {"_id": ObjectId(item_id)},
        {"$set": {"is_checked": new_checked, "updated_at": now}},
    )
    action = "item_checked" if new_checked else "item_unchecked"
    await log_activity(db, list_id=list_id, user_id=str(user["_id"]), user_email=user["email"],
                       action=action, meta={"item_id": item_id, "item_name": doc.get("name")})
    doc["is_checked"] = new_checked
    doc["updated_at"] = now
    doc["_id"] = str(doc["_id"])
    return ItemResponse(**doc)


@router.delete("/checked", status_code=status.HTTP_204_NO_CONTENT)
async def clear_checked_items(list_id: str, db=Depends(get_database), user=Depends(get_current_user)):
    await ensure_list_access(db, list_id, str(user["_id"]))
    await db["items"].delete_many({"list_id": list_id, "is_checked": True})
    await log_activity(db, list_id=list_id, user_id=str(user["_id"]), user_email=user["email"],
                       action="items_cleared")
    return


class MoveItemRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    target_list_id: str


@router.patch("/{item_id}/move", response_model=ItemResponse)
async def move_item(
    list_id: str,
    item_id: str,
    body: MoveItemRequest,
    db=Depends(get_database),
    user=Depends(get_current_user),
):
    """Move an item to a different list. User must have access to both lists."""
    if body.target_list_id == list_id:
        raise HTTPException(status_code=400, detail="Target list must differ from the current list")
    await ensure_list_access(db, list_id, str(user["_id"]))
    await ensure_list_access(db, body.target_list_id, str(user["_id"]))

    doc = await db["items"].find_one({"_id": ObjectId(item_id), "list_id": list_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Item not found")

    now = datetime.utcnow()
    new_position = await db["items"].count_documents({"list_id": body.target_list_id})
    await db["items"].update_one(
        {"_id": ObjectId(item_id)},
        {"$set": {"list_id": body.target_list_id, "position": new_position, "updated_at": now}},
    )

    item_name = doc.get("name")
    await log_activity(db, list_id=list_id, user_id=str(user["_id"]), user_email=user["email"],
                       action="item_moved_out",
                       meta={"item_id": item_id, "item_name": item_name, "target_list_id": body.target_list_id})
    await log_activity(db, list_id=body.target_list_id, user_id=str(user["_id"]), user_email=user["email"],
                       action="item_moved_in",
                       meta={"item_id": item_id, "item_name": item_name, "from_list_id": list_id})

    doc["list_id"] = body.target_list_id
    doc["updated_at"] = now
    doc["_id"] = str(doc["_id"])
    return ItemResponse(**doc)


@router.put("/{item_id}", response_model=ItemResponse)
async def update_item(list_id: str, item_id: str, payload: ItemUpdate,
                      db=Depends(get_database), user=Depends(get_current_user)):
    await ensure_list_access(db, list_id, str(user["_id"]))
    updates = payload.model_dump(exclude_unset=True)
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")
    updates["updated_at"] = datetime.utcnow()
    await db["items"].update_one(
        {"_id": ObjectId(item_id), "list_id": list_id},
        {"$set": updates},
    )
    doc = await db["items"].find_one({"_id": ObjectId(item_id), "list_id": list_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Item not found")
    doc["_id"] = str(doc["_id"])
    return ItemResponse(**doc)


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_item(list_id: str, item_id: str, db=Depends(get_database), user=Depends(get_current_user)):
    await ensure_list_access(db, list_id, str(user["_id"]))
    doc = await db["items"].find_one({"_id": ObjectId(item_id), "list_id": list_id}, {"name": 1})
    await db["items"].delete_one({"_id": ObjectId(item_id), "list_id": list_id})
    if doc:
        await log_activity(db, list_id=list_id, user_id=str(user["_id"]), user_email=user["email"],
                           action="item_deleted", meta={"item_id": item_id, "item_name": doc.get("name")})
    return
