# ============================================================================
# FILE: api/cache.py
# ============================================================================
import redis
import json
import pickle
import logging
from typing import Optional, List, Dict, Any
from config import config

logger = logging.getLogger(__name__)

class CacheClient:
    """Redis cache client for the API."""
    
    def __init__(self):
        try:
            self.client = redis.Redis(
                host=config.redis_host,
                port=config.redis_port,
                password=config.redis_password if config.redis_password else None,
                decode_responses=False,  # We'll handle encoding manually
                socket_connect_timeout=5,
                socket_timeout=5
            )
            # Test connection
            self.client.ping()
            logger.info(f"Connected to Redis: {config.redis_host}:{config.redis_port}")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            logger.warning("Cache will be disabled - API will work without caching")
            self.client = None
    
    def get_query_vector(self, query_text: str) -> Optional[List[float]]:
        """Get cached embedding vector for a query."""
        if not self.client:
            return None
        
        try:
            key = f"query-vector:{query_text}"
            cached = self.client.get(key)
            if cached:
                logger.debug(f"Cache HIT: query-vector for '{query_text[:50]}...'")
                return pickle.loads(cached)
            logger.debug(f"Cache MISS: query-vector for '{query_text[:50]}...'")
            return None
        except Exception as e:
            logger.error(f"Error getting query vector from cache: {e}")
            return None
    
    def set_query_vector(self, query_text: str, vector: List[float]):
        """Cache embedding vector for a query."""
        if not self.client:
            return
        
        try:
            key = f"query-vector:{query_text}"
            self.client.setex(
                key,
                config.cache_ttl_vector,
                pickle.dumps(vector)
            )
            logger.debug(f"Cache SET: query-vector for '{query_text[:50]}...'")
        except Exception as e:
            logger.error(f"Error setting query vector in cache: {e}")
    
    def get_reco_list(self, artwork_id: str) -> Optional[List[str]]:
        """Get cached recommendation list for an artwork."""
        if not self.client:
            return None
        
        try:
            key = f"reco-list:{artwork_id}"
            cached = self.client.get(key)
            if cached:
                logger.debug(f"Cache HIT: reco-list for {artwork_id}")
                return json.loads(cached)
            logger.debug(f"Cache MISS: reco-list for {artwork_id}")
            return None
        except Exception as e:
            logger.error(f"Error getting reco list from cache: {e}")
            return None
    
    def set_reco_list(self, artwork_id: str, reco_ids: List[str]):
        """Cache recommendation list for an artwork."""
        if not self.client:
            return
        
        try:
            key = f"reco-list:{artwork_id}"
            self.client.setex(
                key,
                config.cache_ttl_reco_list,
                json.dumps(reco_ids)
            )
            logger.debug(f"Cache SET: reco-list for {artwork_id}")
        except Exception as e:
            logger.error(f"Error setting reco list in cache: {e}")
    
    def get_artwork_docs(self, artwork_ids: List[str]) -> Dict[str, Optional[Dict[str, Any]]]:
        """Get cached artwork documents (bulk operation)."""
        if not self.client:
            return {aid: None for aid in artwork_ids}
        
        try:
            keys = [f"artwork-doc:{aid}" for aid in artwork_ids]
            cached_values = self.client.mget(keys)
            
            result = {}
            for aid, cached in zip(artwork_ids, cached_values):
                if cached:
                    result[aid] = json.loads(cached)
                    logger.debug(f"Cache HIT: artwork-doc for {aid}")
                else:
                    result[aid] = None
                    logger.debug(f"Cache MISS: artwork-doc for {aid}")
            
            return result
        except Exception as e:
            logger.error(f"Error getting artwork docs from cache: {e}")
            return {aid: None for aid in artwork_ids}
    
    def set_artwork_docs(self, artworks: List[Dict[str, Any]]):
        """Cache artwork documents (bulk operation)."""
        if not self.client:
            return
        
        try:
            pipeline = self.client.pipeline()
            for artwork in artworks:
                artwork_id = str(artwork['_id'])
                key = f"artwork-doc:{artwork_id}"
                # Convert ObjectId to string for JSON serialization
                artwork_copy = self._serialize_artwork(artwork)
                pipeline.setex(
                    key,
                    config.cache_ttl_artwork_doc,
                    json.dumps(artwork_copy)
                )
            pipeline.execute()
            logger.debug(f"Cache SET: {len(artworks)} artwork docs")
        except Exception as e:
            logger.error(f"Error setting artwork docs in cache: {e}")
    
    def _serialize_artwork(self, artwork: Dict[str, Any]) -> Dict[str, Any]:
        """Convert artwork document for JSON serialization."""
        from bson import ObjectId
        artwork_copy = artwork.copy()
        # Convert ObjectId fields to strings
        if '_id' in artwork_copy and isinstance(artwork_copy['_id'], ObjectId):
            artwork_copy['_id'] = str(artwork_copy['_id'])
        if 'artistId' in artwork_copy and isinstance(artwork_copy['artistId'], ObjectId):
            artwork_copy['artistId'] = str(artwork_copy['artistId'])
        return artwork_copy


# Global cache instance
cache = CacheClient()