# ============================================================================
# FILE: veo-api-service/api/config.py
# ============================================================================
import os

class Config:
    """Configuration for the veo-api-service"""
    
    # GCP Configuration
    GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID", "cedar-defender-475318-r5")
    GCP_REGION = os.getenv("GCP_REGION", "asia-south1")
    
    # MongoDB Configuration
    MONGODB_DATABASE = os.getenv("MONGODB_DATABASE", "test")
    MONGODB_SECRET_NAME = os.getenv("MONGODB_SECRET_NAME", "mongodb-connection-string")
    
    # GCS Configuration
    GCS_VIDEO_BUCKET = os.getenv("GCS_VIDEO_BUCKET", "cedar-defender-veo-videos")
    
    # Signed URL Configuration
    SIGNED_URL_EXPIRATION_HOURS = int(os.getenv("SIGNED_URL_EXPIRATION_HOURS", "1"))

config = Config()