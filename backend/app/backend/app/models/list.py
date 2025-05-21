# models/list.py
# This file defines the GroceryList model used to represent user-created grocery lists.
# It includes fields for title, ownership, shared users, and list items, and supports MongoDB insertion via a dictionary method.

from datetime import datetime, timezone
from bson import objectID
from typing import List, Optional

class GroceryList:
    def __init__(
        self,
        title: str,
        owner_id: objectID,
        items: Optional[List[dict]] =  None,
        shared_with: Optional[List[dict]] = None
        ):
        
        """
        Initialize a GroceryList object.

        Args:
            title (str): Title of the grocery list.
            owner_id (ObjectId): The user ID who owns this list.
            items (Optional[List[dict]], optional): A list of item dictionaries. Defaults to an empty list.
            shared_with (Optional[List[ObjectId]], optional): List of user IDs with access to this list. Defaults to empty list.
        """
        self.title = title
        self.owner_id = owner_id
        self.items = items
        self.shared_with = shared_with
        self.created_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)
        
        
def to_dict(self):
    # Convert the GroceryList object into a dictionary for MongoDB.
    return {
        "title": self.title,
        "owner_id": self.owner_id,
        "items": self.items,
        "shared_with": self.shared_with,
        "created_at": self.created_at,
        "updated_at": self.updated_at
    }
    
    