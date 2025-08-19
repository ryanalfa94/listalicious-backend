# schemas/item.py
# Defines validation and response structure for grocery list items.

# backend/app/schemas/list.py

from typing import Optional
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime

class ItemCreate(BaseModel):
    name: str
    quantity: int
    unit: Optional[str] = None
    note: Optional[str] = None
    is_checked: Optional[bool] = False

class ItemUpdate(BaseModel):
    # forbid unknown fields so bad keys 422 instead of silent ignore
    model_config = ConfigDict(extra="forbid")
    name: Optional[str] = None
    quantity: Optional[int] = None
    unit: Optional[str] = None
    note: Optional[str] = None
    is_checked: Optional[bool] = None

class ItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str = Field(..., alias="_id")
    name: str
    quantity: int
    unit: Optional[str] = None
    note: Optional[str] = None
    is_checked: bool
    list_id: str
    created_at: datetime
    updated_at: datetime