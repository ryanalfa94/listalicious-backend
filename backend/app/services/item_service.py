# services/item_service.py

# services/item_service.py
from datetime import datetime, timezone
from bson import ObjectId
from app.database.database import get_database  # keep imports consistent

db = get_database()

async def add_item_to_list(list_id: str, item_data: dict) -> dict:
    # ensure list exists in grocery_lists
    exists = await db["grocery_lists"].find_one({"_id": ObjectId(list_id)})
    if not exists:
        return None

    now = datetime.now(timezone.utc)
    doc = {
        "name": item_data["name"],
        "quantity": item_data["quantity"],
        "unit": item_data.get("unit"),
        "list_id": list_id,
        "created_at": now,
        "updated_at": now,
    }
    res = await db["items"].insert_one(doc)
    doc["_id"] = str(res.inserted_id)
    return doc


async def get_items(db, list_id: str):
    cursor = db["items"].find({"list_id": list_id}).sort("created_at", -1)
    docs = await cursor.to_list(length=500)
    for d in docs:
        d["_id"] = str(d["_id"])
    return docs

async def create_item(db, list_id: str, payload: dict):
    now = datetime.now(timezone.utc)
    doc = {
        "name": payload["name"],
        "quantity": payload["quantity"],
        "unit": payload.get("unit"),
        "note": payload.get("note"),
        "is_checked": payload.get("is_checked", False),
        "list_id": list_id,
        "created_at": now,
        "updated_at": now,
    }
    res = await db["items"].insert_one(doc)
    doc["_id"] = str(res.inserted_id)
    return doc

async def update_item(db, list_id: str, item_id: str, payload: dict):
    payload["updated_at"] = datetime.now(timezone.utc)
    await db["items"].update_one(
        {"_id": ObjectId(item_id), "list_id": list_id},
        {"$set": payload}
    )
    doc = await db["items"].find_one({"_id": ObjectId(item_id), "list_id": list_id})
    if not doc:
        return None
    doc["_id"] = str(doc["_id"])
    return doc

async def delete_item(db, list_id: str, item_id: str):
    await db["items"].delete_one({"_id": ObjectId(item_id), "list_id": list_id})