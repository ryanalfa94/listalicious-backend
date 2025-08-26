# models/item.py
# This file defines the Item model used to represent individual grocery list items.
# It includes structure, default values, and a helper method to convert the object into a MongoDB-friendly dictionary.

from datetime import datetime, timezone
from typing import Optional

class Item:
    def __init__(
        self,
        name: str,
        quantity: int,
        unit: Optional[str] = None,
        note: Optional[str] = None,
        is_checked: bool = False
    ):
        self.name = name
        self.quantity = quantity
        self.unit = unit
        self.note = note
        self.is_checked = is_checked
        self.created_at = datetime.now(timezone.utc)

    def to_dict(self):
        return {
            "name": self.name,
            "quantity": self.quantity,
            "unit": self.unit,
            "note": self.note,
            "is_checked": self.is_checked,
            "created_at": self.created_at
        }     