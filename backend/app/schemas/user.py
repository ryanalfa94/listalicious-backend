# schemas/user.py

from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator, ConfigDict
from typing import Optional
from datetime import datetime
import re


# Input schema for user registration
class UserCreate(BaseModel):
    email: EmailStr
    # max_length=128: bcrypt only reads the first 72 bytes — passing a huge
    # string wastes CPU before that check even runs.
    password: str = Field(min_length=8, max_length=128)
    username: Optional[str] = Field(None, max_length=50)

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if not re.search(r"[A-Za-z]", v):
            raise ValueError("Password must contain at least one letter.")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one digit.")
        return v


# Input schema for login requests
class UserLogin(BaseModel):
    email: EmailStr
    password: str


# Input schema for profile updates (PATCH /me)
class UserUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    username: Optional[str] = Field(None, max_length=50)


# Input schema for changing password while authenticated (POST /auth/change-password)
class ChangePasswordRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    current_password: str
    new_password: str = Field(min_length=8, max_length=128)
    confirm_new_password: Optional[str] = None

    @field_validator("new_password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if not re.search(r"[A-Za-z]", v):
            raise ValueError("Password must contain at least one letter.")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one digit.")
        return v

    @model_validator(mode="after")
    def confirm_match(self) -> "ChangePasswordRequest":
        if self.confirm_new_password is not None and self.new_password != self.confirm_new_password:
            raise ValueError("Passwords do not match.")
        return self


# Input schema for changing email address while authenticated (POST /auth/change-email)
class ChangeEmailRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    new_email: EmailStr
    password: str  # current password required to confirm identity


# Output schema for sending user data back (e.g., after login or register)
class UserResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str = Field(..., alias="_id")
    email: EmailStr
    username: Optional[str] = None
    email_verified: bool = False
    created_at: datetime
    updated_at: datetime
