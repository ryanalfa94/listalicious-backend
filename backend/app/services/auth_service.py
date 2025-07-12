# services/auth_service.py
# Business logic for user registration

from fastapi import HTTPException, status
from app.schemas.user import UserCreate, UserResponse
from app.models.user import User
from app.database.database import user_collection
from passlib.context import CryptContext
from bson import ObjectId

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


from fastapi import HTTPException, status
from datetime import datetime
from bson import ObjectId

async def register_user(user_data: UserCreate) -> UserResponse:
    # 1. Check if email already exists
    existing_user = await user_collection.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # 2. Hash the password
    hashed_password = pwd_context.hash(user_data.password)

    # 3. Create a timestamp
    now = datetime.utcnow()

    # 4. Build the user dictionary for MongoDB
    user_dict = {
        "email": user_data.email,
        "username": user_data.username,
        "hashed_password": hashed_password,
        "created_at": now,
        "updated_at": now
    }

    # 5. Insert into MongoDB
    try:
        result = await user_collection.insert_one(user_dict)
    except Exception as e:
        print("MongoDB insert failed:", e)
        raise HTTPException(status_code=500, detail="Database error")

    user_dict["_id"] = str(result.inserted_id)

    # 6. Build response safely
    try:
        return UserResponse(**user_dict)
    except Exception as e:
        print("Failed to build UserResponse:", e)
        raise HTTPException(status_code=500, detail="Invalid user response")
