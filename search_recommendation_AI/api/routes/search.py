# ============================================================================
# FILE: api/routes/search.py (Corrected)
# ============================================================================
import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

# --- ADD THESE IMPORTS ---
from fastapi.responses import JSONResponse
from utils.serialization import safe_serialize
# --- END IMPORTS ---

from cache import cache
from mongo_client import mongo_client
from vertex_ai_client import vertex_ai_client
from config import config # Import config
# (Removed the circular import of _fetch_artworks_with_cache)

logger = logging.getLogger(__name__)

router = APIRouter()


class SearchRequest(BaseModel):
    """Request model for search endpoint."""
    query_text: str = Field(..., min_length=1, max_length=500, description="Search query text")
    filters: Optional[Dict[str, Any]] = Field(None, description="Optional filters (e.g., artistId, status)")
    num_results: Optional[int] = Field(20, ge=1, le=100, description="Number of results to return")

# --- REMOVED `response_model` FROM DECORATOR ---
@router.post("/search", status_code=status.HTTP_200_OK)
async def search_artworks(request: SearchRequest):
    """
    Search for artworks using semantic search.
    """
    try:
        logger.info(f"Search request: '{request.query_text[:50]}...' (num_results={request.num_results})")
        
        # Step 1: Get or generate embedding vector
        vector = cache.get_query_vector(request.query_text)
        
        if vector is None:
            logger.debug("Generating embedding for query")
            vector = vertex_ai_client.get_text_embedding(request.query_text)
            # Cache the vector
            cache.set_query_vector(request.query_text, vector)
        
        # Step 2: Convert filters to Vertex AI format
        vertex_filters = _convert_filters(request.filters) if request.filters else None
        
        # Step 3: Search vector database
        try:
            neighbor_ids = vertex_ai_client.find_neighbors_by_vector(
                vector=vector,
                num_neighbors=request.num_results,
                restricts=vertex_filters  # ✅ use restricts
            )

        except RuntimeError as e:
            logger.error(f"Vector Search unavailable: {e}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Vector Search service is currently unavailable. Please try again later."
            )
        
        if not neighbor_ids:
            logger.info("No results found for query")
            # --- Fixed syntax error (removed 'x') ---
            return JSONResponse(
                status_code=200,
                content={
                    "results": [], 
                    "total": 0, 
                    "query": request.query_text
                }
            )
        
        # Step 4: Fetch artwork documents (with caching)
        artworks = _fetch_artworks_with_cache(neighbor_ids) 
        
        # --- THIS IS THE FIX ---
        # Ensure 'artworks' is a list, not None, before len() is called.
        if artworks is None:
            logger.error(f"_fetch_artworks_with_cache returned None for IDs: {neighbor_ids}")
            artworks = [] # Default to an empty list to prevent the crash
        # --- END OF FIX ---

        logger.info(f"Search completed: {len(artworks)} results returned")
        
        # Manually serialize the data and return a JSONResponse
        safe_response = safe_serialize({
            "results": artworks,
            "total": len(artworks),
            "query": request.query_text
        })
        return JSONResponse(status_code=200, content=safe_response)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in search endpoint: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


# --- RESTORED THIS FUNCTION ---
def _convert_filters(filters: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Convert API filters to Vertex AI restricts format.
    """
    vertex_filters = []
    
    # Handle token restricts
    if "artistId" in filters and filters["artistId"]:
        vertex_filters.append({
            "namespace": "artistId",
            "allow_list": [str(filters["artistId"])] # Use allow_list
        })
    
    if "tags" in filters and filters["tags"]:
        tags = filters["tags"] if isinstance(filters["tags"], list) else [filters["tags"]]
        valid_tags = [tag for tag in tags if tag]
        if valid_tags:
            vertex_filters.append({
                "namespace": "tags",
                "allow_list": valid_tags # Use allow_list
            })
    
    if "status" in filters and filters["status"]:
        vertex_filters.append({
            "namespace": "status",
            "allow_list": [filters["status"]] # Use allow_list
        })
    
    # Note: True numeric range filtering (e.g., price < 1000) is more complex
    # and requires the `numeric_filter` argument, not `filter`.
    if "price_max" in filters or "likeCount_min" in filters:
        logger.warning("Numeric filters are not fully implemented in this version.")

    
    logger.debug(f"Converted filters: {vertex_filters}")
    return vertex_filters


# --- RESTORED THIS FUNCTION ---
def _fetch_artworks_with_cache(artwork_ids: List[str]) -> List[Dict[str, Any]]:
    """
    Fetch artworks with caching support.
    
    Args:
        artwork_ids: List of artwork IDs
    
    Returns:
        List of artwork documents (ordered by input IDs)
    """
    # Step 1: Check cache
    cached_docs = cache.get_artwork_docs(artwork_ids)
    
    # Step 2: Identify missing docs
    missing_ids = [aid for aid, doc in cached_docs.items() if doc is None]
    
    # Step 3: Fetch missing from MongoDB
    fetched_artworks = []
    if missing_ids:
        logger.debug(f"Fetching {len(missing_ids)} artworks from MongoDB")
        fetched_artworks = mongo_client.fetch_artworks_by_ids(missing_ids)
        
        # Cache the fetched documents
        if fetched_artworks:
            cache.set_artwork_docs(fetched_artworks)
    
    # Step 4: Combine cached and fetched results
    # Create a lookup dict for fetched artworks
    fetched_dict = {str(art['_id']): art for art in fetched_artworks}
    
    # Build final result list (preserving order)
    result = []
    for aid in artwork_ids:
        doc = cached_docs.get(aid) or fetched_dict.get(aid)
        if doc:
            # Ensure _id is string for JSON serialization
            # This check is a bit redundant now that we use safe_serialize
            # but it doesn't hurt.
            if '_id' not in doc or isinstance(doc.get('_id'), str):
                result.append(doc)
            else:
                # This import is slow, but safe_serialize handles it
                from cache import CacheClient 
                result.append(CacheClient()._serialize_artwork(doc)) 
                
    return result

