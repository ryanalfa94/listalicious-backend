# schemas/item.py
# Defines validation and response structure for grocery list items.

# backend/app/schemas/list.py

from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime

class ItemCreate(BaseModel):
    name: str
    quantity: int
    unit: Optional[str] = None

class ItemResponse(BaseModel):
    id: str = Field(..., alias="_id")
    name: str
    quantity: int
    unit: str
    list_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        allow_population_by_field_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        orm_mode = True
