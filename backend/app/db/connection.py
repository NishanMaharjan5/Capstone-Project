from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import os

load_dotenv()

MONGODB_URL = os.getenv("MONGODB_URL")
DATABASE_NAME = os.getenv("DATABASE_NAME")

client = AsyncIOMotorClient(MONGODB_URL)
db = client[DATABASE_NAME]

# Collections
receipts_collection = db["receipts"]
users_collection = db["users"]
budgets_collection = db["budgets"]
trips_collection = db["trips"]
monthly_budgets_collection = db["monthly_budgets"]