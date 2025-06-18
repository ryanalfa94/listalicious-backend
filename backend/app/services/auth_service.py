# services/auth_service.py
# Business logic for user registration

from fastapi import HTTPException, status
from app.schemas.user import UserCreate, UserResponse
from app.models.user import User
from app.database.database import user_collection
from passlib.context import CryptContext
from bson import ObjectId

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

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

    # 3. Create a User model instance
    user = User(
        email=user_data.email,
        hashed_password=hashed_password,
        username=user_data.username
    )

    # 4. Insert into MongoDB
    result = await user_collection.insert_one(user.to_dict())
    user_id = str(result.inserted_id)

    # 5. Return response (exclude password)
    return UserResponse(
        id=user_id,
        email=user.email,
        username=user.username,
        created_at=user.created_at,
        updated_at=user.updated_at
    )
