# schemas/list.py
# Defines validation and response structure for grocery lists.

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class GroceryListCreate(BaseModel):
    title: str
    
class GroceryListResponse(BaseModel):
    id: str = Field(..., alias="_id")
    title: str
    owner_id: str
    items: List[dict]
    shared_with: List[str]
    created_at: datetime
    updated_at: datetime
    
    class config:
        allow_population_by_field_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }