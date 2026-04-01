# schemas/list.py

from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
from datetime import datetime


class GroceryListCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)


class GroceryListUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)


class GroceryListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: str = Field(..., alias="_id")
    title: str
    owner_id: str
    items: List[dict] = []
    shared_with: List[str] = []
    archived: bool = False
    created_at: datetime
    updated_at: datetime
