# ============================================================================
# FILE: veo-api-service/api/mongo_client.py
# ============================================================================
from google.cloud import secretmanager
from pymongo import MongoClient
from .config import config

_mongo_client = None

def get_secret(secret_name: str) -> str:
    """Fetch secret from Google Secret Manager"""
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{config.GCP_PROJECT_ID}/secrets/{secret_name}/versions/latest"
    response = client.access_secret_version(request={"name": name})
    return response.payload.data.decode("UTF-8")

def get_mongo_client():
    """
    Get MongoDB client singleton.
    This can be used as a FastAPI dependency.
    """
    global _mongo_client
    
    if _mongo_client is None:
        mongodb_uri = get_secret(config.MONGODB_SECRET_NAME)
        _mongo_client = MongoClient(mongodb_uri)
    
    return _mongo_client[config.MONGODB_DATABASE]