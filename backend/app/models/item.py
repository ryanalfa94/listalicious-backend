# models/item.py
# This file defines the Item model used to represent individual grocery list items.
# It includes structure, default values, and a helper method to convert the object into a MongoDB-friendly dictionary.

from datetime import datetime, timezone
from typing import Optional, List

class Item:
    def __init__(
        self,
        name: str,
        quantity: int,
        unit: Optional[str],
        note: Optional[str] = None,
        is_checked: bool = False
        ):
        
        """
        Initialize a grocery list item.

        Args:
            name (str): The name of the grocery item (e.g., 'Milk').
            quantity (int): The quantity to buy.
            unit (Optional[str]): Unit of measurement (e.g., 'grams', 'pcs').
            note (Optional[str], optional): Additional notes or preferences.
            is_checked (bool, optional): Whether the item has been marked as bought. Defaults to False.
        """
        self.name = name
        self.quantity = quantity
        self.unit = unit
        self.note = note
        self.is_checked = is_checked
        self.created_at = datetime.now(timezone.utc)
    
    
    
def to_dict(self):

    # Convert the Item object to a dictionary suitable for MongoDB storage.

    return {
        "name": self.name,
        "quantity": self.quantity,
        "unit": self.unit,
        "note": self.note,
        "is_checked": self.is_checked,
        "created_at": self.created_at
    }
    
    
        