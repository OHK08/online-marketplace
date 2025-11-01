# ============================================================================
# FILE: api/mongo_client.py
# ============================================================================
import logging
from typing import List, Dict, Any
from pymongo import MongoClient
from bson import ObjectId
from config import config

logger = logging.getLogger(__name__)

class MongoDBClient:
    """MongoDB client for fetching artwork documents."""
    
    def __init__(self):
        try:
            mongodb_uri = config.get_mongodb_uri()
            self.client = MongoClient(mongodb_uri)
            self.db = self.client[config.mongodb_database]
            self.collection = self.db[config.mongodb_collection]
            # Test connection
            self.client.server_info()
            logger.info(f"Connected to MongoDB: {config.mongodb_database}.{config.mongodb_collection}")
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise

    def get_artwork_by_id(self, artwork_id: str) -> Dict[str, Any] | None:
        """Fetch a single artwork document by its ID."""
        try:
            doc = self.collection.find_one({"_id": ObjectId(artwork_id)})
            if not doc:
                logger.warning(f"No artwork found for ID: {artwork_id}")
            return doc
        except Exception as e:
            logger.error(f"Error fetching artwork {artwork_id}: {e}", exc_info=True)
            return None

    def fetch_artworks_by_ids(self, artwork_ids: List[str]) -> List[Dict[str, Any]]:
        """
        Fetch artwork documents by their IDs.
        
        Args:
            artwork_ids: List of artwork ID strings
        
        Returns:
            List of artwork documents
        """
        try:
            # Convert string IDs to ObjectId
            object_ids = [ObjectId(aid) for aid in artwork_ids]
            
            # Query MongoDB
            cursor = self.collection.find({"_id": {"$in": object_ids}})
            artworks = list(cursor)
            
            logger.debug(f"Fetched {len(artworks)} artworks from MongoDB (requested: {len(artwork_ids)})")
            return artworks
        except Exception as e:
            logger.error(f"Error fetching artworks from MongoDB: {e}")
            return []
    
    def close(self):
        """Close MongoDB connection."""
        if self.client:
            self.client.close()
            logger.info("MongoDB connection closed")


# Global MongoDB client instance
mongo_client = MongoDBClient()