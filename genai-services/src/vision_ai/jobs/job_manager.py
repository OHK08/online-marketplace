import uuid
from datetime import datetime
from typing import Optional, Dict, Any
import os
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI")
if not MONGODB_URI:
    raise RuntimeError("MONGODB_URI not found in .env")

# Extract database name from URI
from urllib.parse import urlparse
parsed = urlparse(MONGODB_URI)
DB_NAME = parsed.path[1:] or "genai"  # Default to "genai"

# Sync client
sync_client = MongoClient(MONGODB_URI)
db_sync = sync_client[DB_NAME]  # ← Explicit DB
jobs_collection_sync = db_sync["jobs"]

# Async client (lazy)
async def get_async_collection():
    from motor.motor_asyncio import AsyncIOMotorClient
    async_client = AsyncIOMotorClient(MONGODB_URI)
    db_async = async_client[DB_NAME]
    return db_async["jobs"]

async def create_job(story_data: Dict[str, Any]) -> str:
    collection = await get_async_collection()
    job_id = str(uuid.uuid4())
    doc = {
        "_id": job_id,
        "status": "queued",
        "story": story_data,
        "video_path": None,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    await collection.insert_one(doc)
    return job_id

async def get_job_status(job_id: str) -> Optional[Dict[str, Any]]:
    collection = await get_async_collection()
    job = await collection.find_one({"_id": job_id})
    if job:
        job.pop("_id", None)
    return job

def update_job_sync(job_id: str, updates: Dict[str, Any]):
    updates["updated_at"] = datetime.utcnow()
    jobs_collection_sync.update_one(
        {"_id": job_id},
        {"$set": updates}
    )