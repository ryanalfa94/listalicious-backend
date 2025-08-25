# services/auth_service.py
# Business logic for user registration

from fastapi import HTTPException, status, Depends
from app.schemas.user import UserCreate, UserResponse
from app.models.user import User
from app.database.database import user_collection
from passlib.context import CryptContext
from bson import ObjectId
from passlib.context import CryptContext
from app.database.database import get_user_by_email
from app.services.jwt_service import create_access_token, verify_token
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

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
    
    
    
    
### LOGIN

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def authenticate_user(email: str, password: str):
    user = await get_user_by_email(email)
    if user and pwd_context.verify(password, user["hashed_password"]):
        return user
    return None

async def login_user(email: str, password: str):
    user = await  authenticate_user(email, password)
    if not user:
        return None
    token = create_access_token(data={"sub": user["email"]})
    return token



bearer_scheme = HTTPBearer()

async def get_current_user(token: HTTPAuthorizationCredentials = Depends(bearer_scheme)):
    payload = verify_token(token.credentials)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )
    
    email = payload.get("sub")
    user = await get_user_by_email(email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return user