# schemas/item.py
# Defines validation and response structure for grocery list items.

from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ItemCreate(BaseModel):
    name: str
    quantity: int
    unit: Optional[str] = None
    note: Optional[str] = None
    

class ItemResponse(BaseModel):
    item: str
    quntity: int
    unit: Optional[str] = None
    note: Optional[str] = None
    is_checked: bool
    created_at: datetime
    
    