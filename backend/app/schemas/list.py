# # schemas/list.py
# # Defines validation and response structure for grocery lists.

# schemas/list.py

from pydantic import BaseModel, Field, ConfigDict
from typing import List
from datetime import datetime

class GroceryListCreate(BaseModel):
    title: str

class GroceryListResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        validate_by_name=True,
        json_encoders={datetime: lambda v: v.isoformat()}
    )

    id: str = Field(..., alias="_id")
    title: str
    owner_id: str
    items: List[dict]
    shared_with: List[str]
    created_at: datetime
    updated_at: datetime
