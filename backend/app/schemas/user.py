# schemas/user.py

# Purpose of schemas:
# They’re not used to store data in MongoDB
# They’re used to validate input and shape output for FastAPI
 

# This file defines Pydantic schemas for user-related operations like registration, login, and responses.


from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


# Input schema for user registration
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    username: Optional[str] = None  # optional display name


# Input schema for login requests    
class UserLogin(BaseModel):
    email: EmailStr
    password: str


# Output schema for sending user data back (e.g., after login or register)
class UserResponse(BaseModel):
    # MongoDB stores the user ID as "_id", but we alias it to "id"
    # so that our API response looks clean and frontend-friendly
    id: str = Field(...,alias="_id")
    
    # User's email address (validated as a proper email format)
    email: EmailStr
    
    # Optional display name or nickname
    username: Optional[str] = None
    
    # Timestamp for when the user was created in the database
    created_at: datetime
    
    # Timestamp for the last update to the user document
    updated_at: datetime
    
    # Extra config to handle Mongo + datetime formatting
    class config:
        # Allows FastAPI to accept both "id" and "_id" when populating this model
        # Useful when loading documents from MongoDB (which returns "_id")
        allow_population_by_field_name = True
        
        # Ensures datetime fields are returned as ISO 8601 strings (e.g. "2024-05-20T18:30:00Z")
        # instead of raw Python datetime objects that break JSON serialization
        json_encoder = {
            datetime: lambda v: v.isoformat()
        }

    