# database/database.py
# Connects to MongoDB using Motor (async client)
# Loads credentials and database name from a .env file

from motor.motor_asyncio import AsyncIOMotorClient  # MongoDB async client
import os
from dotenv import load_dotenv  # For reading .env files

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