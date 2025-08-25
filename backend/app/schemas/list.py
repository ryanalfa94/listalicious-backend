# # schemas/list.py
# # Defines validation and response structure for grocery lists.

# schemas/list.py

from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
from datetime import datetime

class GroceryListCreate(BaseModel):
    title: str

class GroceryListUpdate(BaseModel):
    title: Optional[str] = None

class GroceryListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., alias="_id")
    title: str
    owner_id: str
    items: List[dict] = []
    shared_with: List[str] = []
    created_at: datetime
    updated_at: datetime
