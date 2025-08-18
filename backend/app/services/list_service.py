from app.database.database import get_database
from app.models.list import GroceryList
from bson import ObjectId
from datetime import datetime

db = get_database()
list_collection = db["grocery_lists"]

async def create_grocery_list(title: str, owner_id: str) -> dict:
    now = datetime.utcnow()

    doc = {
        "title": title,
        "owner_id": owner_id,
        "items": [],
        "shared_with": [],
        "created_at": now,
        "updated_at": now
    }

    result = await db["grocery_lists"].insert_one(doc)
    doc["_id"] = str(result.inserted_id)  # convert ObjectId to string

    return doc

async def get_my_lists(db, user_id: str):
    cursor = db["grocery_lists"].find({"owner_id": str(user_id)}).sort("created_at", -1)
    docs = await cursor.to_list(length=200)
    for d in docs:
        d["_id"] = str(d["_id"])
    return docs

async def get_list(db, list_id: str):
    doc = await db["grocery_lists"].find_one({"_id": ObjectId(list_id)})
    if not doc:
        return None
    doc["_id"] = str(doc["_id"])
    return doc

async def update_list(db, list_id: str, payload: dict):
    payload["updated_at"] = datetime.utcnow()
    await db["grocery_lists"].update_one({"_id": ObjectId(list_id)}, {"$set": payload})
    return await get_list(db, list_id)

async def delete_list(db, list_id: str):
    await db["grocery_lists"].delete_one({"_id": ObjectId(list_id)})