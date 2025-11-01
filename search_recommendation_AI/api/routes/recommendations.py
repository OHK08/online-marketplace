# ============================================================================
# PATCHED FILE: api/routes/recommendations.py
# ============================================================================
import logging
from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException, Path, Query, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from cache import cache
from mongo_client import mongo_client
from vertex_ai_client import vertex_ai_client
from routes.search import _fetch_artworks_with_cache
from utils.serialization import safe_serialize

logger = logging.getLogger(__name__)

router = APIRouter()


class RecommendationResponse(BaseModel):
    """Response model for recommendations endpoint."""
    recommendations: List[Dict[str, Any]]
    total: int
    source_artwork_id: str


@router.get(
    "/recommendations/{artwork_id}",
    status_code=status.HTTP_200_OK
)
async def get_recommendations(
    artwork_id: str = Path(..., description="Source artwork ID"),
    num_recommendations: int = Query(5, ge=1, le=20, description="Number of recommendations")
):
    """
    Get artwork recommendations based on similarity.
    ...
    """
    try:
        logger.info(f"Recommendations request: artwork_id={artwork_id}, num={num_recommendations}")
        
        # Step 1: Check cache for recommendation list
        reco_ids = cache.get_reco_list(artwork_id)
        
        if reco_ids is None:
            # Generate recommendations
            logger.debug("Generating recommendations via Vector Search")
            try:
                # Request num_recommendations + 1 to account for the source artwork being returned
                reco_ids = vertex_ai_client.find_neighbors_by_id(
                    artwork_id=artwork_id,
                    num_neighbors=num_recommendations + 1
                )
            except RuntimeError as e:
                logger.error(f"Vector Search unavailable: {e}")
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Vector Search service is currently unavailable. Please try again later."
                )
            
            # Cache the recommendation list
            cache.set_reco_list(artwork_id, reco_ids)
        
        # Step 2: Limit to requested number
        reco_ids = reco_ids[:num_recommendations]
        
        if not reco_ids:
            logger.info(f"No recommendations found for artwork {artwork_id}")
            safe_response = safe_serialize({
                "recommendations": [],
                "total": 0,
                "source_artwork_id": artwork_id
            })
            return JSONResponse(status_code=200, content=safe_response)
        
        # Step 3: Fetch artwork documents (with caching)
        artworks = _fetch_artworks_with_cache(reco_ids)
        
        logger.info(f"Recommendations completed: {len(artworks)} results returned")
        safe_response = safe_serialize({
            "recommendations": artworks,
            "total": len(artworks),
            "source_artwork_id": artwork_id
        })
        return JSONResponse(status_code=200, content=safe_response)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in recommendations endpoint: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )