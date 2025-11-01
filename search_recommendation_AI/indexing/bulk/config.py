# ============================================================================
# FILE: indexing/bulk/config.py
# ============================================================================
import os
import tempfile
from pathlib import Path
from dotenv import load_dotenv
from google.cloud import secretmanager
from typing import Optional
import logging

# Load environment variables from secrets/.env file
# Look for .env in: artwork-search-recommendation/secrets/.env
project_root = Path(__file__).parent.parent.parent  # Go up to project root
env_path = project_root / "secrets" / "example.env"
load_dotenv(dotenv_path=env_path)

logger = logging.getLogger(__name__)

class Config:
    """Configuration loader for the bulk indexing job."""
    
    def __init__(self):
        # GCP Configuration
        self.gcp_project_id = os.getenv("GCP_PROJECT_ID", "your-gcp-project-id")
        self.gcp_region = os.getenv("GCP_REGION", "asia-south1")
        
        # MongoDB Configuration
        self.mongodb_secret_name = os.getenv("MONGODB_SECRET_NAME", "mongodb-connection-string")
        self.mongodb_database = os.getenv("MONGODB_DATABASE", "artwork_marketplace_db")
        self.mongodb_collection = os.getenv("MONGODB_COLLECTION", "artworks")
        
        # GCS Configuration
        self.gcs_bucket_name = os.getenv("GCS_BUCKET_NAME", "your-gcp-bucket-name")
        self.gcs_output_path = os.getenv("GCS_OUTPUT_PATH", "embeddings/all_artworks.json")
        
        # Vertex AI Configuration
        self.vertex_ai_location = os.getenv("VERTEX_AI_LOCATION", "asia-south1")
        self.embedding_model = os.getenv("EMBEDDING_MODEL", "multimodalembedding@001")
        self.embedding_dimension = int(os.getenv("EMBEDDING_DIMENSION", "1408"))
        
        # Processing Configuration
        self.mongodb_batch_size = int(os.getenv("MONGODB_BATCH_SIZE", "1000"))
        self.embedding_batch_size = int(os.getenv("EMBEDDING_BATCH_SIZE", "10"))
        self.test_mode = os.getenv("TEST_MODE", "false").lower() == "true"
        self.test_limit = int(os.getenv("TEST_LIMIT", "20"))
        
        # Local temp file for JSONL
        self.local_jsonl_path = os.path.join(tempfile.gettempdir(), "all_artworks.json")
        
    def get_mongodb_uri(self) -> str:
        """Retrieve MongoDB connection string from Secret Manager."""
        try:
            client = secretmanager.SecretManagerServiceClient()
            secret_path = f"projects/{self.gcp_project_id}/secrets/{self.mongodb_secret_name}/versions/latest"
            response = client.access_secret_version(request={"name": secret_path})
            mongodb_uri = response.payload.data.decode("UTF-8")
            return mongodb_uri
        except Exception as e:
            raise RuntimeError(f"Failed to retrieve MongoDB URI from Secret Manager: {e}")
    
    def validate(self):
        """Validate essential configuration values."""
        logger.info(f"Validating configuration...")
        logger.info(f"  GCP_PROJECT_ID: {self.gcp_project_id}")
        logger.info(f"  GCS_BUCKET_NAME: {self.gcs_bucket_name}")
        logger.info(f"  MONGODB_DATABASE: {self.mongodb_database}")
        logger.info(f"  TEST_MODE: {self.test_mode}")
        
        # Check if placeholder values are still being used
        if self.gcp_project_id == "your-gcp-project-id":
            raise ValueError("GCP_PROJECT_ID must be set to a valid project ID. Please set the environment variable or create a .env file.")
        if self.gcs_bucket_name == "your-gcp-bucket-name":
            raise ValueError("GCS_BUCKET_NAME must be set to a valid bucket name. Please set the environment variable or create a .env file.")
        
        logger.info("✅ Configuration validated successfully")