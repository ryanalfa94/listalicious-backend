from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator
from typing import Optional
import re

# ----- Email verification -----

class EmailVerificationSend(BaseModel):
    model_config = ConfigDict(extra="forbid")
    # email override removed — always uses the authenticated user's email

class EmailVerificationToken(BaseModel):
    model_config = ConfigDict(extra="forbid")
    token: str = Field(min_length=16)  # opaque token from email link

# ----- Password reset (logged-out) -----

class ForgotPasswordRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    email: str  # kept as plain str to avoid leaking enumeration via validation errors

class ResetPasswordRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    token: str = Field(min_length=16)
    new_password: str = Field(min_length=8)
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
    def confirm_match(self) -> "ResetPasswordRequest":
        if self.confirm_new_password is not None and self.new_password != self.confirm_new_password:
            raise ValueError("New password and confirmation do not match.")
        return self
