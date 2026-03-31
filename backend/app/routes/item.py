# routes/item.py
from fastapi import APIRouter, HTTPException, Query, status, Depends
from app.database.database import get_database
from app.services.auth_service import get_current_user
from app.services.guards import ensure_list_access, require_verified_email
from app.schemas.item import ItemCreate, ItemUpdate, ItemResponse
from bson import ObjectId
from datetime import datetime

router = APIRouter(prefix="/lists/{list_id}/items", tags=["Items"])


@router.get("", response_model=list[ItemResponse])
async def list_items(
    list_id: str,
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(50, ge=1, le=200, description="Max items to return"),
    db=Depends(get_database),
    user=Depends(get_current_user),
):
    await ensure_list_access(db, list_id, str(user["_id"]))
    cursor = db["items"].find({"list_id": list_id}).sort("created_at", -1).skip(skip).limit(limit)
    docs = await cursor.to_list(length=limit)
    for d in docs:
        d["_id"] = str(d["_id"])
    return [ItemResponse(**d) for d in docs]


@router.post("", response_model=ItemResponse, status_code=status.HTTP_201_CREATED)
async def create_item(list_id: str, item: ItemCreate, db=Depends(get_database), user=Depends(require_verified_email)):
    await ensure_list_access(db, list_id, str(user["_id"]))
    now = datetime.utcnow()
    doc = {
        "name": item.name,
        "quantity": item.quantity,
        "unit": item.unit,
        "note": item.note,
        "is_checked": item.is_checked or False,
        "list_id": list_id,
        "created_at": now,
        "updated_at": now,
    }
    res = await db["items"].insert_one(doc)
    doc["_id"] = str(res.inserted_id)
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
    await db["items"].delete_one({"_id": ObjectId(item_id), "list_id": list_id})
    return
