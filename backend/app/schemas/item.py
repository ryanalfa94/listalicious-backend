# schemas/item.py

from typing import Optional
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime


class ItemCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    quantity: int = Field(ge=1, le=9999)
    unit: Optional[str] = Field(None, max_length=50)
    note: Optional[str] = Field(None, max_length=1000)
    is_checked: Optional[bool] = False


class ItemBulkCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    items: list[ItemCreate] = Field(min_length=1, max_length=50)


class ItemUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    quantity: Optional[int] = Field(None, ge=1, le=9999)
    unit: Optional[str] = Field(None, max_length=50)
    note: Optional[str] = Field(None, max_length=1000)
    is_checked: Optional[bool] = None


class ItemReorderRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    # Ordered list of item IDs — each item's position becomes its index in this list
    order: list[str] = Field(min_length=1, max_length=500)


class ItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
    id: str = Field(..., alias="_id")
    name: str
    quantity: int
    unit: Optional[str] = None
    note: Optional[str] = None
    is_checked: bool
    list_id: str
    position: Optional[int] = None
    created_at: datetime
    updated_at: datetime
