# ============================================================================
# FILE: veo-api-service/api/routes/reels.py
# ============================================================================
from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any
import random
from ..mongo_client import get_mongo_client
from ..gcs_client import generate_signed_url

router = APIRouter()

@router.get("/reels")
async def get_reels(db = Depends(get_mongo_client)) -> List[Dict[str, Any]]:
    """
    Get all artworks that have generated videos.
    
    This endpoint:
    1. Fetches artworks from MongoDB that have a generatedVideoUrl
    2. Converts private gs:// URIs to public signed HTTPS URLs
    3. Returns a shuffled list of video metadata
    
    Returns:
        List[Dict]: Array of artwork objects with public video URLs
    """
    try:
        # Query MongoDB for artworks with generated videos
        artworks_collection = db["artworks"]
        
        # Fetch documents where generatedVideoUrl exists
        # Project only the fields we need for the frontend
        cursor = artworks_collection.find(
            {"generatedVideoUrl": {"$exists": True}},
            {
                "_id": 1,
                "title": 1,
                "artistName": 1,
                "generatedVideoUrl": 1
            }
        )
        
        # Convert cursor to list
        artworks = list(cursor)
        
        # Convert ObjectId to string and generate signed URLs
        results = []
        for artwork in artworks:
            try:
                # Convert ObjectId to string for JSON serialization
                artwork["_id"] = str(artwork["_id"])
                
                # Convert private GCS URI to public signed URL
                private_uri = artwork["generatedVideoUrl"]
                public_url = generate_signed_url(private_uri)
                artwork["generatedVideoUrl"] = public_url
                
                results.append(artwork)
                
            except Exception as e:
                # Log error but continue processing other artworks
                print(f"Error processing artwork {artwork.get('_id')}: {str(e)}")
                continue
        
        # Shuffle the results for variety
        random.shuffle(results)
        
        return results
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch reels: {str(e)}"
        )