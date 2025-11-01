# ============================================================================
# FILE: api/config.py
# ============================================================================
import os
from pathlib import Path
from dotenv import load_dotenv
from google.cloud import secretmanager
from typing import Optional
import logging

# Load environment variables from secrets/.env file
project_root = Path(__file__).parent.parent  # Go up to project root
env_path = project_root / "secrets" / "example.env"
load_dotenv(dotenv_path=env_path)

logger = logging.getLogger(__name__)

class Config:
    """Configuration loader for the API service."""
    
    def __init__(self):
        # ------------------------------
        # GCP Configuration
        # ------------------------------
        self.gcp_project_id = os.getenv("GCP_PROJECT_ID", "your-gcp-project-id")
        self.gcp_region = os.getenv("GCP_REGION", "asia-south1")
        
        # ------------------------------
        # MongoDB Configuration
        # ------------------------------
        self.mongodb_secret_name = os.getenv("MONGODB_SECRET_NAME", "mongodb-connection-string")
        self.mongodb_database = os.getenv("MONGODB_DATABASE", "artwork_marketplace_db")
        self.mongodb_collection = os.getenv("MONGODB_COLLECTION", "artworks")
        
        # ------------------------------
        # Redis Configuration
        # ------------------------------
        self.redis_host = os.getenv("REDIS_HOST", "localhost")
        self.redis_port = int(os.getenv("REDIS_PORT", "6379"))
        self.redis_password = os.getenv("REDIS_PASSWORD", "")
        
        # ------------------------------
        # Vertex AI Configuration
        # ------------------------------
        self.vertex_ai_location = os.getenv("VERTEX_AI_LOCATION", "asia-south1")
        self.vertex_ai_endpoint_id = os.getenv("VERTEX_AI_ENDPOINT_ID", "")
        self.vertex_ai_deployed_index_id = os.getenv("VERTEX_AI_DEPLOYED_INDEX_ID", "")
        self.vertex_ai_public_domain = os.getenv("VERTEX_AI_PUBLIC_DOMAIN", "")
        self.embedding_model = os.getenv("EMBEDDING_MODEL", "multimodalembedding@001")
        self.embedding_dimension = int(os.getenv("EMBEDDING_DIMENSION", "1408"))
        
        # ------------------------------
        # Cache TTL Configuration (seconds)
        # ------------------------------
        self.cache_ttl_vector = int(os.getenv("CACHE_TTL_VECTOR", "86400"))       # 24 hours
        self.cache_ttl_reco_list = int(os.getenv("CACHE_TTL_RECO_LIST", "43200")) # 12 hours
        self.cache_ttl_artwork_doc = int(os.getenv("CACHE_TTL_ARTWORK_DOC", "3600")) # 1 hour
        
        # ------------------------------
        # API Configuration
        # ------------------------------
        self.default_num_neighbors = int(os.getenv("DEFAULT_NUM_NEIGHBORS", "20"))
        self.max_num_neighbors = int(os.getenv("MAX_NUM_NEIGHBORS", "100"))
        
    # ------------------------------
    # Secret Manager helper
    # ------------------------------
    def get_mongodb_uri(self) -> str:
        """Retrieve MongoDB connection string from Secret Manager."""
        try:
            client = secretmanager.SecretManagerServiceClient()
            secret_path = f"projects/{self.gcp_project_id}/secrets/{self.mongodb_secret_name}/versions/latest"
            response = client.access_secret_version(request={"name": secret_path})
            mongodb_uri = response.payload.data.decode("UTF-8")
            return mongodb_uri
        except Exception as e:
            logger.error(f"Failed to retrieve MongoDB URI from Secret Manager: {e}")
            raise RuntimeError(f"Failed to retrieve MongoDB URI from Secret Manager: {e}")
    
    # ------------------------------
    # Validation
    # ------------------------------
    def validate(self):
        """Validate essential configuration values."""
        logger.info("Validating API configuration...")
        logger.info(f"  GCP_PROJECT_ID: {self.gcp_project_id}")
        logger.info(f"  MONGODB_DATABASE: {self.mongodb_database}")
        logger.info(f"  REDIS_HOST: {self.redis_host}:{self.redis_port}")
        if len(self.vertex_ai_endpoint_id) > 50:
            logger.info(f"  VERTEX_AI_ENDPOINT_ID: {self.vertex_ai_endpoint_id[:50]}...")
        else:
            logger.info(f"  VERTEX_AI_ENDPOINT_ID: {self.vertex_ai_endpoint_id}")
        logger.info(f"  VERTEX_AI_PUBLIC_DOMAIN: {self.vertex_ai_public_domain}")
        
        if self.gcp_project_id == "your-gcp-project-id":
            raise ValueError("GCP_PROJECT_ID must be set")
        if not self.vertex_ai_endpoint_id:
            logger.warning("⚠️  VERTEX_AI_ENDPOINT_ID not set - Vector Search will not work!")
        if not self.vertex_ai_deployed_index_id:
            logger.warning("⚠️  VERTEX_AI_DEPLOYED_INDEX_ID not set - Vector Search will not work!")
        if not self.vertex_ai_public_domain:
            logger.warning("⚠️  VERTEX_AI_PUBLIC_DOMAIN not set - MatchServiceClient will fail!")
        
        logger.info("✅ Configuration validated")

# Global config instance
config = Config()
