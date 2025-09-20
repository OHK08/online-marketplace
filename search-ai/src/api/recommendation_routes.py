# api/recommendation_routes.py
"""
Recommendation API routes with cultural intelligence
Follows your existing enhanced_search_routes patterns for consistency
"""

from fastapi import APIRouter, HTTPException, Query, Body, BackgroundTasks
from typing import Dict, List, Optional, Any
import logging
import time

from src.models.recommendation_models import (
    RecommendationRequest, RecommendationResponse, UserPreferenceRequest,
    SeasonalRecommendationRequest, BatchRecommendationRequest, BatchRecommendationResponse,
    RecommendationType, CulturalSimilarityConfig, RecommendationAnalytics
)
from src.models.cultural_models import CraftType, IndianRegion, Festival, CulturalSignificance
from src.services.recommendation_service import recommendation_service
from src.config.settings import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/recommendations", tags=["Cultural Recommendations"])

# Item-based recommendation endpoints

@router.post("/similar", response_model=RecommendationResponse)
async def get_similar_items(request: RecommendationRequest):
    """
    Get culturally similar items based on an existing item
    
    This endpoint finds items similar to a given item using:
    - Cultural context analysis (craft type, region, materials)
    - Festival and seasonal relevance  
    - Traditional techniques and significance
    - Regional diversity for cross-cultural discovery
    """
    try:
        logger.info(f"Getting similar items for: {request.item_id} with types: {[rt.value for rt in request.recommendation_types]}")
        
        response = await recommendation_service.get_item_recommendations(request)
        
        return response
        
    except Exception as e:
        logger.error(f"Error in similar items recommendation: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Similar items recommendation failed: {str(e)}"
        )

@router.get("/similar/{item_id}")
async def get_similar_items_simple(
    item_id: str,
    limit: int = Query(5, ge=1, le=20, description="Number of recommendations"),
    recommendation_types: Optional[str] = Query(
        None, 
        description="Comma-separated recommendation types (cultural_similarity,regional_discovery,festival_seasonal)"
    ),
    similarity_threshold: float = Query(0.3, ge=0.0, le=1.0, description="Minimum similarity threshold"),
    enable_diversity: bool = Query(True, description="Enable regional/craft diversity"),
    seasonal_boost: bool = Query(True, description="Apply seasonal festival boost"),
    exclude_items: Optional[str] = Query(None, description="Comma-separated item IDs to exclude")
):
    """
    GET endpoint for similar items with query parameters
    """
    try:
        # Parse recommendation types
        rec_types = [RecommendationType.CULTURAL_SIMILARITY]  # Default
        if recommendation_types:
            rec_types = []
            for rt in recommendation_types.split(','):
                rt = rt.strip()
                if rt in RecommendationType.__members__.values():
                    rec_types.append(RecommendationType(rt))
        
        # Parse excluded items
        excluded_ids = []
        if exclude_items:
            excluded_ids = [item.strip() for item in exclude_items.split(',')]
        
        # Build request
        request = RecommendationRequest(
            item_id=item_id,
            recommendation_types=rec_types,
            limit=limit,
            similarity_threshold=similarity_threshold,
            enable_diversity=enable_diversity,
            seasonal_boost=seasonal_boost,
            exclude_item_ids=excluded_ids if excluded_ids else None
        )
        
        response = await recommendation_service.get_item_recommendations(request)
        
        return response
        
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=f"Invalid parameter: {str(ve)}")
    except Exception as e:
        logger.error(f"Error in GET similar items: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Recommendation failed: {str(e)}")

# User preference-based recommendations
@router.post("/test-lookup/{item_id}")
async def test_item_lookup(item_id: str):
    """Test endpoint to debug item lookup"""
    result = await recommendation_service.test_item_lookup(item_id)
    return {"debug_info": result}

@router.post("/for-user", response_model=RecommendationResponse)
async def get_user_recommendations(request: UserPreferenceRequest):
    """
    Get personalized recommendations based on user preferences and history
    
    This endpoint generates recommendations using:
    - User interaction history and preferences
    - Preferred craft types, regions, and festivals
    - Budget and material preferences
    - Diversity factor for exploration vs exploitation
    """
    try:
        logger.info(f"Getting user recommendations for user: {request.user_id}")
        
        response = await recommendation_service.get_user_recommendations(request)
        
        return response
        
    except Exception as e:
        logger.error(f"Error in user recommendations: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"User recommendations failed: {str(e)}"
        )

# Seasonal and festival recommendations

@router.post("/seasonal", response_model=RecommendationResponse)
async def get_seasonal_recommendations(request: SeasonalRecommendationRequest):
    """
    Get seasonal and festival-aware recommendations
    
    This endpoint finds items relevant to:
    - Current and upcoming festivals
    - Regional festival preferences
    - Gift items and decorative pieces
    - Seasonal craft traditions
    """
    try:
        logger.info(f"Getting seasonal recommendations for festival: {request.current_festival}")
        
        response = await recommendation_service.get_seasonal_recommendations(request)
        
        return response
        
    except Exception as e:
        logger.error(f"Error in seasonal recommendations: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Seasonal recommendations failed: {str(e)}"
        )

@router.get("/seasonal")
async def get_current_seasonal_recommendations(
    limit: int = Query(10, ge=1, le=30, description="Number of recommendations"),
    region: Optional[str] = Query(None, description="Preferred region for festival items"),
    include_gifts: bool = Query(True, description="Include gift items"),
    include_decorative: bool = Query(True, description="Include decorative items"),
    festival: Optional[str] = Query(None, description="Specific festival focus")
):
    """
    GET endpoint for current seasonal recommendations
    """
    try:
        # Parse region
        region_preference = None
        if region and region in IndianRegion.__members__.values():
            region_preference = IndianRegion(region)
        
        # Parse festival
        festival_preference = None
        if festival and festival in Festival.__members__.values():
            festival_preference = Festival(festival)
        
        # Build request
        request = SeasonalRecommendationRequest(
            current_festival=festival_preference,
            region_preference=region_preference,
            include_gift_items=include_gifts,
            include_decorative=include_decorative,
            limit=limit
        )
        
        response = await recommendation_service.get_seasonal_recommendations(request)
        
        return response
        
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=f"Invalid parameter: {str(ve)}")
    except Exception as e:
        logger.error(f"Error in GET seasonal recommendations: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Seasonal recommendations failed: {str(e)}")

# Regional discovery endpoints

@router.get("/discover/{region}")
async def discover_regional_crafts(
    region: str,
    limit: int = Query(10, ge=1, le=30, description="Number of items to discover"),
    craft_types: Optional[str] = Query(None, description="Comma-separated craft types to focus on"),
    exclude_common: bool = Query(True, description="Exclude very common items"),
    cultural_depth: float = Query(0.5, ge=0.0, le=1.0, description="Focus on traditional vs contemporary")
):
    """
    Discover crafts from a specific Indian region
    
    This endpoint helps users explore:
    - Traditional crafts from specific regions
    - Regional specialties and techniques
    - Cross-cultural craft connections
    - Hidden gems from artisan communities
    """
    try:
        # Validate region
        if region not in IndianRegion.__members__.values():
            raise HTTPException(status_code=400, detail=f"Invalid region: {region}")
        
        region_enum = IndianRegion(region)
        
        # Parse craft types if provided
        craft_type_filters = []
        if craft_types:
            for ct in craft_types.split(','):
                ct = ct.strip()
                if ct in CraftType.__members__.values():
                    craft_type_filters.append(CraftType(ct))
        
        # Create a user preference request focused on regional discovery
        request = UserPreferenceRequest(
            preferred_regions=[region_enum],
            preferred_craft_types=craft_type_filters if craft_type_filters else None,
            recommendation_types=[RecommendationType.REGIONAL_DISCOVERY],
            limit=limit,
            diversity_factor=cultural_depth
        )
        
        response = await recommendation_service.get_user_recommendations(request)
        
        return response
        
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=f"Invalid parameter: {str(ve)}")
    except Exception as e:
        logger.error(f"Error in regional discovery: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Regional discovery failed: {str(e)}")

# Batch recommendation endpoints

@router.post("/batch", response_model=BatchRecommendationResponse)
async def get_batch_recommendations(request: BatchRecommendationRequest):
    """
    Get recommendations for multiple items in a single request
    
    Useful for:
    - Bulk recommendation generation
    - Homepage "You might also like" sections
    - Cart completion suggestions
    - Email campaign personalization
    """
    try:
        logger.info(f"Getting batch recommendations for {len(request.item_ids)} items")
        
        start_time = time.time()
        results_by_item = {}
        successful = 0
        failed = 0
        
        for item_id in request.item_ids:
            try:
                # Create individual recommendation request
                individual_request = RecommendationRequest(
                    item_id=item_id,
                    recommendation_types=request.recommendation_types,
                    limit=request.recommendations_per_item,
                    similarity_threshold=request.similarity_threshold,
                    enable_diversity=True
                )
                
                # Get recommendations
                item_response = await recommendation_service.get_item_recommendations(individual_request)
                results_by_item[item_id] = item_response
                successful += 1
                
            except Exception as e:
                logger.warning(f"Failed to get recommendations for item {item_id}: {e}")
                # Create empty response for failed item
                results_by_item[item_id] = RecommendationResponse(
                    source_item_id=item_id,
                    total_recommendations=0,
                    recommendations=[],
                    recommendation_types_used=request.recommendation_types
                )
                failed += 1
        
        # Deduplication across items if requested
        if request.enable_cross_item_deduplication:
            results_by_item = _deduplicate_across_items(results_by_item)
        
        # Calculate batch-level insights
        batch_insights = _calculate_batch_insights(results_by_item)
        
        processing_time = (time.time() - start_time) * 1000
        
        return BatchRecommendationResponse(
            total_items_processed=len(request.item_ids),
            successful_recommendations=successful,
            failed_recommendations=failed,
            recommendations_by_item=results_by_item,
            processing_time_ms=round(processing_time, 2),
            most_common_regions=batch_insights.get("common_regions", []),
            most_common_craft_types=batch_insights.get("common_craft_types", []),
            diversity_across_batch=batch_insights.get("diversity_score", 0.0)
        )
        
    except Exception as e:
        logger.error(f"Error in batch recommendations: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Batch recommendations failed: {str(e)}"
        )

# Analytics and insights endpoints

@router.get("/analytics")
async def get_recommendation_analytics():
    """
    Get recommendation service analytics and performance metrics
    """
    try:
        stats = recommendation_service.get_stats()
        
        # Create analytics response
        analytics = RecommendationAnalytics(
            total_recommendations_served=stats.get("recommendations_served", 0),
            recommendation_type_distribution={},  # Would be populated with real data
            average_cultural_similarity_score=0.75,  # Placeholder
            regional_distribution={},  # Would be populated with real data
            craft_type_distribution={},  # Would be populated with real data
            seasonal_recommendation_effectiveness={},  # Would be populated with real data
            average_response_time_ms=stats.get("avg_response_time_ms", 0.0),
            cache_hit_rate=stats.get("cache_hits", 0) / max(stats.get("recommendations_served", 1), 1),
            fallback_usage_rate=stats.get("fallback_used", 0) / max(stats.get("recommendations_served", 1), 1),
            recommendation_diversity_score=0.65,  # Placeholder
            cross_cultural_discovery_rate=0.25  # Placeholder
        )
        
        return {
            "status": "ok",
            "analytics": analytics,
            "raw_stats": stats
        }
        
    except Exception as e:
        logger.error(f"Error getting recommendation analytics: {str(e)}")
        return {
            "status": "error",
            "error": str(e)
        }

@router.get("/health")
async def recommendation_health_check():
    """Health check for recommendation service functionality"""
    try:
        # Test basic functionality
        stats = recommendation_service.get_stats()
        
        # Check if service is responding
        health_status = {
            "status": "healthy",
            "service_active": True,
            "cache_operational": True,
            "cultural_analysis_available": True,
            "content_based_engine_ready": True,
            "stats": {
                "total_served": stats.get("recommendations_served", 0),
                "avg_response_time_ms": stats.get("avg_response_time_ms", 0.0),
                "cache_size": stats.get("cache_size", 0)
            }
        }
        
        return health_status
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "service_active": False
        }

# Configuration and management endpoints

@router.get("/config/similarity")
async def get_similarity_config():
    """Get current cultural similarity configuration"""
    try:
        config = CulturalSimilarityConfig()
        return {
            "status": "ok",
            "config": config.dict(),
            "description": "Weights used for cultural similarity calculations"
        }
    except Exception as e:
        logger.error(f"Error getting similarity config: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Config retrieval failed: {str(e)}")

@router.delete("/cache")
async def clear_recommendation_cache():
    """Clear recommendation service cache"""
    try:
        recommendation_service.clear_cache()
        
        return {
            "status": "cache_cleared",
            "message": "Recommendation service cache cleared successfully"
        }
        
    except Exception as e:
        logger.error(f"Error clearing recommendation cache: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to clear cache: {str(e)}"
        )

# Cultural category exploration endpoints

@router.get("/explore/craft-types")
async def explore_by_craft_type(
    craft_type: str = Query(..., description="Craft type to explore"),
    limit: int = Query(15, ge=1, le=50, description="Number of items"),
    region_preference: Optional[str] = Query(None, description="Preferred region"),
    traditional_focus: float = Query(0.7, ge=0.0, le=1.0, description="Traditional vs contemporary balance")
):
    """
    Explore items by specific craft type with cultural context
    """
    try:
        # Validate craft type
        if craft_type not in CraftType.__members__.values():
            raise HTTPException(status_code=400, detail=f"Invalid craft type: {craft_type}")
        
        craft_enum = CraftType(craft_type)
        
        # Parse region preference
        region_enum = None
        if region_preference and region_preference in IndianRegion.__members__.values():
            region_enum = IndianRegion(region_preference)
        
        # Create user preference request focused on craft type
        request = UserPreferenceRequest(
            preferred_craft_types=[craft_enum],
            preferred_regions=[region_enum] if region_enum else None,
            recommendation_types=[RecommendationType.CULTURAL_SIMILARITY],
            limit=limit,
            diversity_factor=1.0 - traditional_focus  # Higher traditional focus = lower diversity
        )
        
        response = await recommendation_service.get_user_recommendations(request)
        
        return response
        
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=f"Invalid parameter: {str(ve)}")
    except Exception as e:
        logger.error(f"Error in craft type exploration: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Craft type exploration failed: {str(e)}")

# Helper functions for batch processing

def _deduplicate_across_items(results_by_item: Dict[str, RecommendationResponse]) -> Dict[str, RecommendationResponse]:
    """Remove duplicate recommendations across different source items"""
    seen_item_ids = set()
    
    for item_id, response in results_by_item.items():
        filtered_recommendations = []
        
        for recommendation in response.recommendations:
            if recommendation.id not in seen_item_ids:
                filtered_recommendations.append(recommendation)
                seen_item_ids.add(recommendation.id)
        
        # Update the response with filtered recommendations
        response.recommendations = filtered_recommendations
        response.total_recommendations = len(filtered_recommendations)
    
    return results_by_item

def _calculate_batch_insights(results_by_item: Dict[str, RecommendationResponse]) -> Dict[str, Any]:
    """Calculate insights across all recommendations in the batch"""
    region_counter = {}
    craft_type_counter = {}
    total_recommendations = 0
    unique_regions = set()
    unique_craft_types = set()
    
    for response in results_by_item.values():
        total_recommendations += len(response.recommendations)
        
        for rec in response.recommendations:
            if rec.cultural_context:
                if rec.cultural_context.region:
                    region = rec.cultural_context.region.value
                    region_counter[region] = region_counter.get(region, 0) + 1
                    unique_regions.add(region)
                
                if rec.cultural_context.craft_type:
                    craft_type = rec.cultural_context.craft_type.value
                    craft_type_counter[craft_type] = craft_type_counter.get(craft_type, 0) + 1
                    unique_craft_types.add(craft_type)
    
    # Calculate diversity score
    diversity_score = 0.0
    if total_recommendations > 0:
        region_diversity = len(unique_regions) / max(total_recommendations, 1)
        craft_diversity = len(unique_craft_types) / max(total_recommendations, 1)
        diversity_score = (region_diversity + craft_diversity) / 2
    
    # Get most common regions and craft types
    most_common_regions = sorted(region_counter.keys(), key=region_counter.get, reverse=True)[:5]
    most_common_craft_types = sorted(craft_type_counter.keys(), key=craft_type_counter.get, reverse=True)[:5]
    
    return {
        "common_regions": most_common_regions,
        "common_craft_types": most_common_craft_types,
        "diversity_score": diversity_score
    }