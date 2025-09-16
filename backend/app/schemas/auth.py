from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional
from datetime import datetime

class AuthUser(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str = Field(..., alias="_id")
    email: EmailStr
    username: Optional[str] = None
    created_at: datetime
    updated_at: datetime

class AuthResponse(BaseModel):
    user: AuthUser
    access_token: str
    token_type: str = "bearer"
