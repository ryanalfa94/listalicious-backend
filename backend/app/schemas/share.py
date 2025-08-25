from pydantic import BaseModel, EmailStr, ConfigDict

class ShareRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    email: EmailStr

class ShareResponse(BaseModel):
    list_id: str
    shared_with: list[str]
