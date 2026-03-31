# database/database.py
# Connects to MongoDB using Motor (async client)
# Loads credentials and database name from a .env file

from motor.motor_asyncio import AsyncIOMotorClient  # MongoDB async client
import os
from dotenv import load_dotenv  # For reading .env files
from bson.objectid import ObjectId

# Load environment variables from a .env file in your root directory
load_dotenv()

# Get the MongoDB URI and DB name from environment variables (fallback to defaults if missing)
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "listalicious")

# Create an async MongoDB client
client = AsyncIOMotorClient(MONGO_URI)

# Connect to the specified database
db = client[MONGO_DB_NAME]

# Collections we'll be using across the app
user_collection = db["users"]
list_collection = db["lists"]
item_collection = db["items"]
grocery_lists_collection = db["grocery_lists"]
items_collection = db["items"]


async def get_user_by_email(email: str):
    return await user_collection.find_one({"email": email})

def get_database():
    return db

async def init_indexes():
    """Create indexes for performance and TTL auto-cleanup. Safe to call on every startup (idempotent)."""
    # email_verifications: fast token lookup, per-user queries, and auto-delete expired docs
    await db["email_verifications"].create_index("token_hash", unique=True)
    await db["email_verifications"].create_index("user_id")
    await db["email_verifications"].create_index("expires_at", expireAfterSeconds=0)

    # password_resets: same pattern
    await db["password_resets"].create_index("token_hash", unique=True)
    await db["password_resets"].create_index("user_id")
    await db["password_resets"].create_index("expires_at", expireAfterSeconds=0)

    # revoked_tokens: fast JTI lookup and auto-delete once token expires
    await db["revoked_tokens"].create_index("jti", unique=True)
    await db["revoked_tokens"].create_index("expires_at", expireAfterSeconds=0)

    # users: fast email lookup (used on every login and forgot-password)
    await db["users"].create_index("email", unique=True)

    # grocery_lists: fast lookup by owner and by shared_with membership
    await db["grocery_lists"].create_index("owner_id")
    await db["grocery_lists"].create_index("shared_with")

    # items: fast lookup by list_id (used in every item query)
    await db["items"].create_index("list_id")