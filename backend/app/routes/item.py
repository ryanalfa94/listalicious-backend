# routes/item.py

from fastapi import APIRouter, HTTPException, status, Depends
from app.schemas.item import ItemCreate, ItemResponse
from app.database.database import get_database


from bson import ObjectId
from datetime import datetime

router = APIRouter(
    prefix="/items",
    tags=["Items"]
)

@router.post("/{list_id}", response_model=ItemResponse)
async def add_item_to_list(list_id: str, item: ItemCreate, db=Depends(get_database)):
    list_obj = await db["grocery_lists"].find_one({"_id": ObjectId(list_id)})
    if not list_obj:
        raise HTTPException(status_code=404, detail="List not found")

    new_item = {
        "name": item.name,
        "quantity": item.quantity,
        "unit": item.unit,
        "list_id": list_id,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }

    result = await db.items.insert_one(new_item)
    new_item["_id"] = str(result.inserted_id)
    return ItemResponse(**new_item)

@router.get("/{list_id}", response_model=list[ItemResponse])
async def get_items_in_list(list_id: str, db=Depends(get_database)):
    cursor = db.items.find({"list_id": list_id})
    items = await cursor.to_list(length=100)
    for item in items:
        item["_id"] = str(item["_id"])
    return [ItemResponse(**item) for item in items]