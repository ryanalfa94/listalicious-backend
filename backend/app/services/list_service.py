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