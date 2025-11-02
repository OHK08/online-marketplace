# ============================================================================
# FILE: config.py
# ============================================================================
"""
Configuration module for veo-generator Cloud Run Job.
Loads all required environment variables.
"""
import os

# GCP Configuration
GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID", "cedar-defender-475318-r5")
GCP_REGION = os.getenv("GCP_REGION", "us-central1")

# MongoDB Configuration
MONGODB_DATABASE = os.getenv("MONGODB_DATABASE", "test")
MONGODB_SECRET_NAME = os.getenv("MONGODB_SECRET_NAME", "mongodb-connection-string")

# Video Generation Configuration
VIDEO_BATCH_SIZE = int(os.getenv("VIDEO_BATCH_SIZE", "40"))
TEST_MODE = os.getenv("TEST_MODE", "false").lower() == "true"

# GCS Configuration
GCS_VIDEO_BUCKET = os.getenv("GCS_VIDEO_BUCKET", "cedar-defender-veo-videos")

# Veo Model Configuration
VEO_MODEL_ID = "publishers/google/models/veo-3.0-fast-generate-001"
VEO_LOCATION = "us-central1"
VEO_API_ENDPOINT = f"https://{VEO_LOCATION}-aiplatform.googleapis.com/v1"

# Video Generation Parameters
VIDEO_DURATION_SECONDS = 5
VIDEO_RESOLUTION = "720p"  # Options: 480p, 720p, 1080p
VIDEO_SAMPLE_COUNT = 1  # Number of videos to generate (1-2)
VIDEO_GENERATE_AUDIO = True  # Generate audio for videos

# Polling Configuration
OPERATION_POLL_INTERVAL = 10  # seconds between status checks
OPERATION_MAX_WAIT_TIME = 300  # 5 minutes max wait per video

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

def validate_config():
    """Validate that all required configuration is present."""
    required_vars = [
        ("GCP_PROJECT_ID", GCP_PROJECT_ID),
        ("GCP_REGION", GCP_REGION),
        ("MONGODB_DATABASE", MONGODB_DATABASE),
        ("GCS_VIDEO_BUCKET", GCS_VIDEO_BUCKET),
    ]
    
    missing = [name for name, value in required_vars if not value]
    if missing:
        raise ValueError(f"Missing required environment variables: {', '.join(missing)}")
    
    print(f"✅ Configuration validated")
    print(f"   Project: {GCP_PROJECT_ID}")
    print(f"   Region: {GCP_REGION}")
    print(f"   Database: {MONGODB_DATABASE}")
    print(f"   Bucket: {GCS_VIDEO_BUCKET}")
    print(f"   Batch Size: {VIDEO_BATCH_SIZE}")
    print(f"   Test Mode: {TEST_MODE}")