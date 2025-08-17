# services/item_service.py

# services/item_service.py
from datetime import datetime
from bson import ObjectId
from app.database.database import get_database  # keep imports consistent

db = get_database()

async def add_item_to_list(list_id: str, item_data: dict) -> dict:
    # ensure list exists in grocery_lists
    exists = await db["grocery_lists"].find_one({"_id": ObjectId(list_id)})
    if not exists:
        return None

    now = datetime.utcnow()
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
