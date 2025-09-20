# services/recommendation_service.py
import time
import asyncio
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from collections import defaultdict, Counter

from src.services.cultural_service import cultural_service
from src.services.search_service import search_items
from src.database.qdrant_client import qdrant
from src.algorithms.content_based import content_based_recommender, SimilarityResult
from src.models.recommendation_models import (
    RecommendationRequest, RecommendationResponse, RecommendationItem, RecommendationScore,
    UserPreferenceRequest, SeasonalRecommendationRequest, BatchRecommendationRequest,
    RecommendationType, SimilarityMetric
)
from src.models.cultural_models import (
    CulturalContext, CulturalAnalysisRequest, CraftType, IndianRegion, Festival, CulturalSignificance
)
from src.config.settings import settings
from src.utils.logger import recommendation_logger as logger
from qdrant_client.models import ScrollRequest

class CulturalRecommendationService:
    """
    Main recommendation service integrating cultural intelligence with content-based filtering
    Enhanced with comprehensive logging and complete implementations
    """
    
    def __init__(self):
        logger.info("Initializing Cultural Recommendation Service")
        
        self.cache = {}  # Simple in-memory cache matching your cultural service
        self.cache_ttl = 1800  # 30 minutes
        
        # Performance stats matching your patterns
        self.stats = {
            "recommendations_served": 0,
            "cache_hits": 0,
            "cultural_analyses_performed": 0,
            "avg_response_time_ms": 0.0,
            "fallback_used": 0,
            "failed_requests": 0,
            "empty_responses": 0
        }
        
        logger.info("Cultural Recommendation Service initialized successfully")

    async def get_item_recommendations(self, request: RecommendationRequest) -> RecommendationResponse:
        """
        Main method for item-based recommendations using cultural intelligence
        Enhanced with detailed logging for troubleshooting
        """
        start_time = time.time()
        request_id = f"req_{int(start_time * 1000)}"
        
        logger.info(
            f"[{request_id}] Starting item recommendation request - "
            f"item_id={request.item_id}, rec_types={[rt.value for rt in request.recommendation_types]}, "
            f"limit={request.limit}, similarity_threshold={request.similarity_threshold}"
        )
        
        # Check cache first
        cache_key = f"rec_{request.item_id}_{'-'.join([rt.value for rt in request.recommendation_types])}_{request.limit}"
        if cache_key in self.cache:
            cache_entry = self.cache[cache_key]
            if time.time() - cache_entry["timestamp"] < self.cache_ttl:
                self.stats["cache_hits"] += 1
                processing_time = (time.time() - start_time) * 1000
                
                logger.debug(f"[{request_id}] Using cached recommendations - processing_time_ms={processing_time}")
                logger.log_cache_operation("read", "recommendation", cache_key, hit=True)
                
                cache_entry["response"].processing_time_ms = round(processing_time, 2)
                return cache_entry["response"]
        
        logger.log_cache_operation("read", "recommendation", cache_key, hit=False)
        
        try:
            # Step 1: Get source item with cultural context
            logger.debug(f"[{request_id}] Fetching source item with cultural context")
            source_item = await self._get_item_with_cultural_context(request.item_id, request_id)
            
            if not source_item:
                error_msg = f"Source item {request.item_id} not found"
                logger.warning(f"[{request_id}] {error_msg}")
                self.stats["failed_requests"] += 1
                return self._create_empty_response(request, error_msg)
            
            logger.info(
                f"[{request_id}] Source item retrieved successfully - "
                f"cultural_context={self._get_cultural_context_summary(source_item.get('cultural_context'))}"
            )
            
            # Step 2: Get candidate items for recommendations
            logger.debug(f"[{request_id}] Fetching candidate items")
            candidate_items = await self._get_candidate_items(
                source_item, 
                exclude_ids=request.exclude_item_ids or [],
                request_id=request_id
            )
            
            if not candidate_items:
                error_msg = "No candidate items found"
                logger.warning(f"[{request_id}] {error_msg}")
                self.stats["empty_responses"] += 1
                return self._create_empty_response(request, error_msg)
            
            logger.info(f"[{request_id}] Found {len(candidate_items)} candidate items")
            
            # Step 3: Generate recommendations based on types requested
            all_recommendations = []
            recommendation_stats = defaultdict(int)
            
            for rec_type in request.recommendation_types:
                logger.debug(f"[{request_id}] Generating {rec_type.value} recommendations")
                
                try:
                    type_recommendations = await self._generate_recommendations_by_type(
                        rec_type, source_item, candidate_items, request, request_id
                    )
                    all_recommendations.extend(type_recommendations)
                    recommendation_stats[rec_type] += len(type_recommendations)
                    
                    logger.debug(
                        f"[{request_id}] Generated {len(type_recommendations)} {rec_type.value} recommendations"
                    )
                    
                except Exception as e:
                    logger.error(
                        f"[{request_id}] Failed to generate {rec_type.value} recommendations: {str(e)} - "
                        f"error_type={type(e).__name__}, recommendation_type={rec_type.value}"
                    )
                    continue
            
            logger.info(
                f"[{request_id}] Generated {len(all_recommendations)} total recommendations across {len(recommendation_stats)} types"
            )
            
            # Step 4: Deduplicate and rank
            logger.debug(f"[{request_id}] Deduplicating and ranking recommendations")
            final_recommendations = self._deduplicate_and_rank_recommendations(
                all_recommendations, request.limit, request_id
            )
            
            # Step 5: Create response
            processing_time = (time.time() - start_time) * 1000
            response = RecommendationResponse(
                source_item_id=request.item_id,
                total_recommendations=len(final_recommendations),
                recommendations=final_recommendations,
                recommendation_types_used=request.recommendation_types,
                processing_time_ms=round(processing_time, 2),
                cultural_diversity_stats=self._calculate_diversity_stats(final_recommendations),
                seasonal_recommendations_count=recommendation_stats.get(RecommendationType.FESTIVAL_SEASONAL, 0),
                cross_cultural_recommendations_count=recommendation_stats.get(RecommendationType.CROSS_CULTURAL, 0),
                cache_hits=0,  # Not a cache hit
                recommendation_confidence=self._calculate_overall_confidence(final_recommendations)
            )
            
            # Step 6: Cache the response
            self.cache[cache_key] = {
                "response": response,
                "timestamp": time.time()
            }
            logger.log_cache_operation("write", "recommendation", cache_key)
            
            # Step 7: Update stats and log final results
            self._update_stats(processing_time / 1000)
            
            logger.info(
                f"[{request_id}] Recommendation request completed successfully - "
                f"final_count={len(final_recommendations)}, processing_time_ms={processing_time}, "
                f"confidence={response.recommendation_confidence}, "
                f"diversity_regions={response.cultural_diversity_stats.get('unique_regions', 0)}, "
                f"diversity_crafts={response.cultural_diversity_stats.get('unique_craft_types', 0)}"
            )
            
            logger.log_recommendation_request(
                "item_based", 
                request.item_id, 
                [rt.value for rt in request.recommendation_types], 
                processing_time / 1000, 
                len(final_recommendations)
            )
            
            return response
            
        except Exception as e:
            processing_time = (time.time() - start_time) * 1000
            logger.log_error_with_traceback(e, f"[{request_id}] item recommendation request")
            self.stats["failed_requests"] += 1
            return self._create_error_response(request, str(e))

    async def get_user_recommendations(self, request: UserPreferenceRequest) -> RecommendationResponse:
        """
        Generate recommendations based on user preferences and interaction history
        Enhanced with detailed logging
        """
        start_time = time.time()
        request_id = f"user_req_{int(start_time * 1000)}"
        
        logger.info(
            f"[{request_id}] Starting user preference recommendation request - "
            f"user_id={request.user_id}, "
            f"preferred_regions={[r.value for r in request.preferred_regions] if request.preferred_regions else None}, "
            f"preferred_crafts={[c.value for c in request.preferred_craft_types] if request.preferred_craft_types else None}, "
            f"interaction_history_count={len(request.user_interaction_history) if request.user_interaction_history else 0}"
        )
        
        try:
            # Step 1: Get user's preferred items for analysis
            logger.debug(f"[{request_id}] Analyzing user interaction history")
            user_items = []
            
            if request.user_interaction_history:
                for i, item_id in enumerate(request.user_interaction_history[-10:]):  # Last 10 interactions
                    logger.debug(f"[{request_id}] Fetching user interaction item {i+1}/10: {item_id}")
                    item = await self._get_item_with_cultural_context(item_id, request_id)
                    if item:
                        user_items.append(item)
                    else:
                        logger.warning(f"[{request_id}] Could not retrieve interaction item: {item_id}")
            
            logger.info(f"[{request_id}] Retrieved {len(user_items)} user interaction items")
            
            # Step 2: Create user cultural profile from preferences and history
            logger.debug(f"[{request_id}] Creating user cultural profile")
            user_cultural_profile = self._create_user_cultural_profile(request, user_items, request_id)
            
            # Step 3: Get candidate items based on user preferences
            logger.debug(f"[{request_id}] Fetching candidate items for user preferences")
            candidate_items = await self._get_candidate_items_for_user(
                request, user_cultural_profile, request_id
            )
            
            if not candidate_items:
                error_msg = "No suitable items found for user preferences"
                logger.warning(f"[{request_id}] {error_msg}")
                self.stats["empty_responses"] += 1
                return self._create_empty_response(request, error_msg)
            
            logger.info(f"[{request_id}] Found {len(candidate_items)} candidate items for user")
            
            # Step 4: Generate recommendations based on user profile
            logger.debug(f"[{request_id}] Generating user-based recommendations")
            recommendations = await self._generate_user_based_recommendations(
                user_cultural_profile, candidate_items, request, request_id
            )
            
            # Step 5: Apply diversity and ranking
            logger.debug(f"[{request_id}] Applying diversity preferences and ranking")
            final_recommendations = self._apply_user_diversity_preferences(
                recommendations, request.diversity_factor, request.limit, request_id
            )
            
            processing_time = (time.time() - start_time) * 1000
            response = RecommendationResponse(
                source_item_id=None,
                total_recommendations=len(final_recommendations),
                recommendations=final_recommendations,
                recommendation_types_used=request.recommendation_types,
                processing_time_ms=round(processing_time, 2),
                cultural_diversity_stats=self._calculate_diversity_stats(final_recommendations)
            )
            
            self._update_stats(processing_time / 1000)
            
            logger.info(
                f"[{request_id}] User recommendation request completed successfully - "
                f"final_count={len(final_recommendations)}, processing_time_ms={processing_time}, "
                f"diversity_factor={request.diversity_factor}"
            )
            
            logger.log_recommendation_request(
                "user_based", 
                request.user_id or "anonymous", 
                [rt.value for rt in request.recommendation_types], 
                processing_time / 1000, 
                len(final_recommendations)
            )
            
            return response
            
        except Exception as e:
            processing_time = (time.time() - start_time) * 1000
            logger.log_error_with_traceback(e, f"[{request_id}] user preference recommendation request")
            self.stats["failed_requests"] += 1
            return self._create_error_response(request, str(e))

    async def get_seasonal_recommendations(self, request: SeasonalRecommendationRequest) -> RecommendationResponse:
        """
        Generate seasonal/festival-aware recommendations using cultural service
        Enhanced with detailed logging
        """
        start_time = time.time()
        request_id = f"seasonal_req_{int(start_time * 1000)}"
        
        logger.info(
            f"[{request_id}] Starting seasonal recommendation request - "
            f"current_festival={request.current_festival.value if request.current_festival else None}, "
            f"upcoming_festivals={[f.value for f in request.upcoming_festivals] if request.upcoming_festivals else None}, "
            f"region_preference={request.region_preference.value if request.region_preference else None}, "
            f"limit={request.limit}"
        )
        
        try:
            # Step 1: Get current seasonal context from cultural service
            logger.debug(f"[{request_id}] Fetching seasonal context from cultural service")
            seasonal_context = cultural_service.get_seasonal_context()
            
            logger.debug(
                f"[{request_id}] Retrieved seasonal context - "
                f"active_festivals={seasonal_context.get('active_festivals', [])}"
            )
            
            # Step 2: Determine active festivals
            active_festivals = []
            if request.current_festival:
                active_festivals.append(request.current_festival)
                logger.debug(f"[{request_id}] Added current festival: {request.current_festival.value}")
            
            if request.upcoming_festivals:
                active_festivals.extend(request.upcoming_festivals)
                logger.debug(f"[{request_id}] Added upcoming festivals: {[f.value for f in request.upcoming_festivals]}")
            
            # If no specific festivals provided, use seasonal context
            if not active_festivals:
                seasonal_festivals = [
                    Festival(f) for f in seasonal_context.get("active_festivals", [])
                    if f in Festival.__members__.values()
                ]
                active_festivals = seasonal_festivals
                logger.debug(f"[{request_id}] Using seasonal context festivals: {[f.value for f in active_festivals]}")
            
            if not active_festivals:
                logger.warning(f"[{request_id}] No active festivals found for seasonal recommendations")
            
            # Step 3: Get all available items
            logger.debug(f"[{request_id}] Fetching all available items with cultural context")
            all_items = await self._get_all_items_with_cultural_context(request_id)
            
            if not all_items:
                error_msg = "No items available for seasonal analysis"
                logger.warning(f"[{request_id}] {error_msg}")
                self.stats["empty_responses"] += 1
                return self._create_empty_response(request, error_msg)
            
            logger.info(f"[{request_id}] Retrieved {len(all_items)} items for seasonal analysis")
            
            # Step 4: Filter for seasonal relevance
            logger.debug(f"[{request_id}] Finding seasonal recommendations using content-based recommender")
            seasonal_items = content_based_recommender.find_seasonal_recommendations(
                all_items, active_festivals, request.limit * 2  # Get more for filtering
            )
            
            logger.info(f"[{request_id}] Content-based recommender found {len(seasonal_items)} seasonal items")
            
            # Step 5: Apply additional filters
            logger.debug(f"[{request_id}] Applying seasonal filters")
            filtered_items = self._apply_seasonal_filters(seasonal_items, request, request_id)
            
            logger.info(f"[{request_id}] After seasonal filtering: {len(filtered_items)} items remain")
            
            # Step 6: Convert to RecommendationItem format
            recommendations = []
            for item_data, similarity_result in filtered_items[:request.limit]:
                rec_item = self._create_recommendation_item(
                    item_data, similarity_result, RecommendationType.FESTIVAL_SEASONAL, 
                    SimilarityMetric.FESTIVAL_SEASONAL, request_id
                )
                recommendations.append(rec_item)
            
            processing_time = (time.time() - start_time) * 1000
            response = RecommendationResponse(
                source_item_id=None,
                total_recommendations=len(recommendations),
                recommendations=recommendations,
                recommendation_types_used=[RecommendationType.FESTIVAL_SEASONAL],
                processing_time_ms=round(processing_time, 2),
                seasonal_recommendations_count=len(recommendations),
                cultural_diversity_stats=self._calculate_diversity_stats(recommendations)
            )
            
            self._update_stats(processing_time / 1000)
            
            logger.info(
                f"[{request_id}] Seasonal recommendation request completed successfully - "
                f"final_count={len(recommendations)}, processing_time_ms={processing_time}, "
                f"festivals_matched={len(active_festivals)}"
            )
            
            logger.log_recommendation_request(
                "seasonal", 
                f"festivals_{len(active_festivals)}", 
                ["festival_seasonal"], 
                processing_time / 1000, 
                len(recommendations)
            )
            
            return response
            
        except Exception as e:
            processing_time = (time.time() - start_time) * 1000
            logger.log_error_with_traceback(e, f"[{request_id}] seasonal recommendation request")
            self.stats["failed_requests"] += 1
            return self._create_error_response(request, str(e))

    # COMPLETE MISSING HELPER METHODS

    async def _get_candidate_items_for_user(
        self, 
        request: UserPreferenceRequest, 
        user_cultural_profile: Dict,
        request_id: str = ""
    ) -> List[Dict[str, Any]]:
        """Get candidate items based on user preferences"""
        logger.debug(f"[{request_id}] Getting candidate items for user preferences")
        
        try:
            # Get all available items
            all_items = await self._get_all_items_with_cultural_context(request_id)
            
            if not all_items:
                logger.warning(f"[{request_id}] No items available for user filtering")
                return []
            
            filtered_items = []
            
            for item in all_items:
                cultural_context = item.get("cultural_context")
                if not cultural_context:
                    continue
                
                # Apply craft type filter
                if request.preferred_craft_types:
                    if cultural_context.craft_type not in request.preferred_craft_types:
                        continue
                
                # Apply region filter  
                if request.preferred_regions:
                    if cultural_context.region not in request.preferred_regions:
                        continue
                
                # Apply festival filter
                if request.preferred_festivals:
                    festival_overlap = set(cultural_context.festival_relevance) & set(request.preferred_festivals)
                    if not festival_overlap:
                        continue
                
                # Apply budget filter if provided
                if request.budget_range:
                    item_price = item["payload"].get("price", 0)
                    if item_price < request.budget_range.get("min", 0) or item_price > request.budget_range.get("max", float('inf')):
                        continue
                
                filtered_items.append(item)
            
            logger.info(f"[{request_id}] Filtered {len(all_items)} items to {len(filtered_items)} candidates")
            return filtered_items
            
        except Exception as e:
            logger.error(f"[{request_id}] Error getting user candidate items: {str(e)}")
            return []

    async def _get_all_items_with_cultural_context(self, request_id: str = "") -> List[Dict[str, Any]]:
        """Get all available items with cultural context"""
        logger.debug(f"[{request_id}] Getting all items with cultural context")
        
        try:
            all_items = []
            offset = None
            batch_size = 500  # Process in batches
            
            while True:
                # Scroll through items in batches
                scroll_results, next_offset = qdrant.scroll(
                    collection_name=settings.COLLECTION_NAME,
                    scroll_filter=None,
                    limit=batch_size,
                    offset=offset,
                    with_payload=True,
                )
                
                if not scroll_results:
                    break
                
                logger.debug(f"[{request_id}] Processing batch of {len(scroll_results)} items")
                
                for point in scroll_results:
                    payload = point.payload or {}
                    item_data = {
                        "id": str(point.id),
                        "text": payload.get("text", ""),
                        "payload": payload,
                        "vector": point.vector if hasattr(point, 'vector') else None
                    }
                    
                    # Add cultural context if missing
                    if "cultural_context" not in payload:
                        # Only analyze a subset to avoid too many API calls
                        if len(all_items) < 100:  # Limit cultural analysis for performance
                            logger.debug(f"[{request_id}] Generating cultural context for item {item_data['id']}")
                            analysis_request = CulturalAnalysisRequest(
                                title=payload.get("title", ""),
                                description=item_data["text"]
                            )
                            cultural_analysis = await cultural_service.analyze_artwork_cultural_context(analysis_request)
                            item_data["cultural_context"] = cultural_analysis.cultural_context
                            self.stats["cultural_analyses_performed"] += 1
                        else:
                            # Use fallback for remaining items
                            item_data["cultural_context"] = cultural_service._enhanced_fallback_analysis(item_data["text"], payload.get("title", ""))
                    else:
                        # Deserialize existing cultural context if it's stored as dict
                        if isinstance(payload["cultural_context"], dict):
                            item_data["cultural_context"] = CulturalContext(**payload["cultural_context"])
                        else:
                            item_data["cultural_context"] = payload["cultural_context"]
                    
                    all_items.append(item_data)
                
                # Check if we have more items
                offset = next_offset
                if not next_offset:
                    break
            
            logger.info(f"[{request_id}] Loaded {len(all_items)} items with cultural context")
            return all_items
            
        except Exception as e:
            logger.error(f"[{request_id}] Error getting all items: {str(e)}")
            return []

    def _create_user_cultural_profile(
        self, 
        request: UserPreferenceRequest, 
        user_items: List[Dict[str, Any]],
        request_id: str = ""
    ) -> Dict[str, Any]:
        """Create user cultural profile from preferences and history"""
        logger.debug(f"[{request_id}] Creating user cultural profile")
        
        profile = {
            "preferred_craft_types": {},
            "preferred_regions": {}, 
            "preferred_festivals": {},
            "preferred_materials": {},
            "cultural_openness": 0.5,
            "interaction_count": len(user_items)
        }
        
        # Extract preferences from explicit user inputs
        if request.preferred_craft_types:
            for craft_type in request.preferred_craft_types:
                profile["preferred_craft_types"][craft_type.value] = 1.0
        
        if request.preferred_regions:
            for region in request.preferred_regions:
                profile["preferred_regions"][region.value] = 1.0
        
        if request.preferred_festivals:
            for festival in request.preferred_festivals:
                profile["preferred_festivals"][festival.value] = 1.0
        
        # Extract patterns from user interaction history
        if user_items:
            craft_counts = {}
            region_counts = {}
            material_counts = {}
            
            for item in user_items:
                cultural_context = item.get("cultural_context")
                if cultural_context:
                    # Count craft types
                    if cultural_context.craft_type:
                        craft_counts[cultural_context.craft_type.value] = craft_counts.get(cultural_context.craft_type.value, 0) + 1
                    
                    # Count regions  
                    if cultural_context.region:
                        region_counts[cultural_context.region.value] = region_counts.get(cultural_context.region.value, 0) + 1
                    
                    # Count materials
                    for material in cultural_context.materials:
                        material_counts[material] = material_counts.get(material, 0) + 1
            
            # Convert counts to preferences (normalize)
            total_items = len(user_items)
            for craft, count in craft_counts.items():
                profile["preferred_craft_types"][craft] = count / total_items
            
            for region, count in region_counts.items():
                profile["preferred_regions"][region] = count / total_items
            
            for material, count in material_counts.items():
                if count >= 2:  # Only include materials seen multiple times
                    profile["preferred_materials"][material] = count / total_items
            
            # Calculate cultural openness (diversity of preferences)
            unique_crafts = len(craft_counts)
            unique_regions = len(region_counts)
            profile["cultural_openness"] = min((unique_crafts + unique_regions) / 10, 1.0)
        
        logger.info(
            f"[{request_id}] User cultural profile created - "
            f"craft_preferences={len(profile['preferred_craft_types'])}, "
            f"region_preferences={len(profile['preferred_regions'])}, "
            f"cultural_openness={profile['cultural_openness']}, "
            f"based_on_items={len(user_items)}"
        )
        
        return profile

    async def _generate_user_based_recommendations(
        self,
        user_cultural_profile: Dict[str, Any],
        candidate_items: List[Dict[str, Any]],
        request: UserPreferenceRequest,
        request_id: str = ""
    ) -> List[RecommendationItem]:
        """Generate recommendations based on user profile"""
        logger.debug(f"[{request_id}] Generating user-based recommendations")
        
        recommendations = []
        
        try:
            for item in candidate_items:
                cultural_context = item.get("cultural_context")
                if not cultural_context:
                    continue
                
                # Calculate user-item compatibility score
                compatibility_score = 0.0
                match_reasons = []
                
                # Craft type compatibility
                if cultural_context.craft_type and cultural_context.craft_type.value in user_cultural_profile["preferred_craft_types"]:
                    craft_score = user_cultural_profile["preferred_craft_types"][cultural_context.craft_type.value]
                    compatibility_score += craft_score * 0.4
                    match_reasons.append(f"Craft preference: {cultural_context.craft_type.value}")
                
                # Region compatibility
                if cultural_context.region and cultural_context.region.value in user_cultural_profile["preferred_regions"]:
                    region_score = user_cultural_profile["preferred_regions"][cultural_context.region.value]
                    compatibility_score += region_score * 0.3
                    match_reasons.append(f"Region preference: {cultural_context.region.value}")
                
                # Festival compatibility
                for festival in cultural_context.festival_relevance:
                    if festival.value in user_cultural_profile["preferred_festivals"]:
                        festival_score = user_cultural_profile["preferred_festivals"][festival.value]
                        compatibility_score += festival_score * 0.2
                        match_reasons.append(f"Festival match: {festival.value}")
                
                # Material compatibility
                for material in cultural_context.materials:
                    if material in user_cultural_profile["preferred_materials"]:
                        material_score = user_cultural_profile["preferred_materials"][material]
                        compatibility_score += material_score * 0.1
                        match_reasons.append(f"Material preference: {material}")
                
                # Cultural exploration bonus
                if user_cultural_profile["cultural_openness"] > 0.5:
                    is_new_craft = cultural_context.craft_type.value not in user_cultural_profile["preferred_craft_types"]
                    is_new_region = cultural_context.region.value not in user_cultural_profile["preferred_regions"]
                    
                    if is_new_craft or is_new_region:
                        exploration_bonus = user_cultural_profile["cultural_openness"] * 0.1
                        compatibility_score += exploration_bonus
                        match_reasons.append("Cultural exploration bonus")
                
                if compatibility_score > 0.1:  # Minimum threshold
                    # Create similarity result
                    similarity_result = SimilarityResult(
                        similarity_score=compatibility_score,
                        cultural_similarity=compatibility_score,
                        vector_similarity=0.0,
                        seasonal_relevance=0.0,
                        regional_match=1.0 if cultural_context.region.value in user_cultural_profile["preferred_regions"] else 0.0,
                        festival_relevance=len([f for f in cultural_context.festival_relevance if f.value in user_cultural_profile["preferred_festivals"]]) / max(len(cultural_context.festival_relevance), 1),
                        match_reasons=match_reasons
                    )
                    
                    # Create recommendation item
                    rec_item = self._create_recommendation_item(
                        item, similarity_result, RecommendationType.CULTURAL_SIMILARITY, 
                        SimilarityMetric.CULTURAL_CONTEXT, request_id
                    )
                    recommendations.append(rec_item)
            
            # Sort by compatibility score
            recommendations.sort(key=lambda x: x.score_breakdown.overall_score, reverse=True)
            
            logger.info(f"[{request_id}] Generated {len(recommendations)} user-based recommendations")
            return recommendations
            
        except Exception as e:
            logger.error(f"[{request_id}] Error generating user-based recommendations: {str(e)}")
            return []

    def _apply_user_diversity_preferences(
        self,
        recommendations: List[RecommendationItem],
        diversity_factor: float,
        limit: int,
        request_id: str = ""
    ) -> List[RecommendationItem]:
        """Apply diversity preferences to recommendations"""
        logger.debug(f"[{request_id}] Applying diversity preferences - diversity_factor={diversity_factor}")
        
        if not recommendations or diversity_factor == 0:
            return recommendations[:limit]
        
        try:
            # Track diversity
            region_counts = {}
            craft_counts = {}
            diversified_recommendations = []
            
            # Sort by score first
            sorted_recs = sorted(recommendations, key=lambda x: x.score_breakdown.overall_score, reverse=True)
            
            for rec in sorted_recs:
                if len(diversified_recommendations) >= limit:
                    break
                
                cultural_context = rec.cultural_context
                if not cultural_context:
                    diversified_recommendations.append(rec)
                    continue
                
                # Check diversity constraints
                region = cultural_context.region.value if cultural_context.region else "unknown"
                craft = cultural_context.craft_type.value if cultural_context.craft_type else "unknown"
                
                region_count = region_counts.get(region, 0)
                craft_count = craft_counts.get(craft, 0)
                
                # Apply diversity factor (higher factor = more diversity enforcement)
                max_same_region = max(1, int(limit * (1 - diversity_factor)))
                max_same_craft = max(1, int(limit * (1 - diversity_factor)))
                
                if region_count < max_same_region and craft_count < max_same_craft:
                    diversified_recommendations.append(rec)
                    region_counts[region] = region_count + 1
                    craft_counts[craft] = craft_count + 1
                elif diversity_factor < 0.8:  # Less strict diversity
                    diversified_recommendations.append(rec)
            
            logger.info(
                f"[{request_id}] Applied diversity preferences - "
                f"original_count={len(recommendations)}, final_count={len(diversified_recommendations)}, "
                f"unique_regions={len(region_counts)}, unique_crafts={len(craft_counts)}"
            )
            
            return diversified_recommendations
            
        except Exception as e:
            logger.error(f"[{request_id}] Error applying diversity preferences: {str(e)}")
            return recommendations[:limit]

    def _apply_seasonal_filters(
        self,
        seasonal_items: List[Tuple[Dict[str, Any], Any]],
        request: SeasonalRecommendationRequest,
        request_id: str = ""
    ) -> List[Tuple[Dict[str, Any], Any]]:
        """Apply additional seasonal filters"""
        logger.debug(f"[{request_id}] Applying seasonal filters")
        
        try:
            filtered_items = []
            
            for item_data, similarity_result in seasonal_items:
                cultural_context = item_data.get("cultural_context")
                if not cultural_context:
                    continue
                
                # Apply region preference filter
                if request.region_preference:
                    if cultural_context.region != request.region_preference:
                        continue
                
                # Apply gift items filter
                if request.include_gift_items:
                    if cultural_context.cultural_significance not in [
                        CulturalSignificance.GIFT_ITEM,
                        CulturalSignificance.FESTIVAL_ITEM,
                        CulturalSignificance.DECORATIVE
                    ]:
                        continue
                
                # Apply decorative items filter  
                if request.include_decorative:
                    if cultural_context.cultural_significance == CulturalSignificance.DAILY_USE:
                        continue
                
                # Apply price range filter if provided
                if request.price_range:
                    item_price = item_data["payload"].get("price", 0)
                    min_price = request.price_range.get("min", 0)
                    max_price = request.price_range.get("max", float('inf'))
                    
                    if item_price < min_price or item_price > max_price:
                        continue
                
                filtered_items.append((item_data, similarity_result))
            
            logger.info(f"[{request_id}] Seasonal filtering: {len(seasonal_items)} -> {len(filtered_items)} items")
            return filtered_items
            
        except Exception as e:
            logger.error(f"[{request_id}] Error applying seasonal filters: {str(e)}")
            return seasonal_items

    # DEBUG METHOD FOR TESTING
    async def get_debug_recommendations(self, item_id: str) -> Dict[str, Any]:
        """Get recommendations with debug info and very low thresholds"""
        logger.info(f"DEBUG: Getting recommendations for {item_id} with minimal thresholds")
        
        # Create request with very permissive settings
        request = RecommendationRequest(
            item_id=item_id,
            recommendation_types=[RecommendationType.CULTURAL_SIMILARITY],
            limit=10,
            similarity_threshold=0.0,  # Accept everything for debugging
            enable_diversity=False  # Disable diversity for debugging
        )
        
        # Get the response
        response = await self.get_item_recommendations(request)
        
        # Add debug information
        debug_info = {
            "request_settings": {
                "similarity_threshold": 0.0,
                "enable_diversity": False,
                "limit": 10
            },
            "response_summary": {
                "total_recommendations": response.total_recommendations,
                "processing_time_ms": response.processing_time_ms,
                "confidence": response.recommendation_confidence
            },
            "recommendations_detail": []
        }
        
        for rec in response.recommendations:
            debug_info["recommendations_detail"].append({
                "id": rec.id,
                "overall_score": rec.score_breakdown.overall_score,
                "cultural_score": rec.score_breakdown.cultural_similarity,
                "vector_score": rec.score_breakdown.vector_similarity,
                "match_reasons": rec.cultural_match_reasons,
                "craft_type": rec.cultural_context.craft_type.value if rec.cultural_context else None,
                "region": rec.cultural_context.region.value if rec.cultural_context else None
            })
        
        return debug_info

    # Enhanced helper methods with logging

    async def _get_item_with_cultural_context(self, item_id: str, request_id: str = "") -> Optional[Dict[str, Any]]:
        """Get item from Qdrant with cultural context analysis - FIXED VERSION"""
        try:
            logger.debug(f"[{request_id}] Searching for item {item_id}")
            
            # Try direct retrieval by UUID first
            try:
                import uuid
                # Ensure proper UUID format
                try:
                    uuid_obj = uuid.UUID(item_id)
                    point_ids = [str(uuid_obj)]
                except ValueError:
                    point_ids = [item_id]
                
                points = qdrant.retrieve(
                    collection_name=settings.COLLECTION_NAME,
                    ids=point_ids,
                    with_payload=True,
                    with_vectors=True
                )
                
                if points and len(points) > 0:
                    point = points[0]
                    payload = point.payload or {}
                    
                    # Handle missing text
                    text = payload.get("text") or payload.get("description") or payload.get("title") or ""
                    if not text:
                        logger.warning(f"[{request_id}] Item {item_id} has no text")
                        return None
                    
                    item_data = {
                        "id": str(point.id),
                        "text": text,
                        "payload": payload,
                        "vector": point.vector if hasattr(point, 'vector') else None
                    }
                    
                    # Add cultural context
                    if "cultural_context" not in payload:
                        # FIX: Handle empty title properly
                        item_title = payload.get("title", "")
                        analysis_request = CulturalAnalysisRequest(
                            title=item_title if item_title else "Untitled Item",
                            description=text
                        )
                        cultural_analysis = await cultural_service.analyze_artwork_cultural_context(analysis_request)
                        item_data["cultural_context"] = cultural_analysis.cultural_context
                        self.stats["cultural_analyses_performed"] += 1
                    else:
                        existing = payload["cultural_context"]
                        item_data["cultural_context"] = CulturalContext(**existing) if isinstance(existing, dict) else existing
                    
                    logger.info(f"[{request_id}] Found item by retrieve: {item_id}")
                    return item_data
                    
            except Exception as retrieve_error:
                logger.warning(f"[{request_id}] Retrieve failed: {str(retrieve_error)}")
            
            # Fallback: Use scroll with proper limit
            logger.debug(f"[{request_id}] Using scroll fallback")
            
            offset = None
            while True:
                points, next_offset = qdrant.scroll(
                    collection_name=settings.COLLECTION_NAME,
                    limit=100,
                    offset=offset,
                    with_payload=True,
                    with_vectors=True
                )
                
                if not points:
                    break
                
                for point in points:
                    if str(point.id) == item_id or point.payload.get("item_id") == item_id:
                        payload = point.payload or {}
                        text = payload.get("text") or payload.get("description") or payload.get("title") or ""
                        
                        if not text:
                            logger.warning(f"[{request_id}] Found {item_id} but no text")
                            return None
                        
                        item_data = {
                            "id": str(point.id),
                            "text": text,
                            "payload": payload,
                            "vector": point.vector if hasattr(point, 'vector') else None
                        }
                        
                        # Add cultural context - FIX: Handle empty title properly
                        if "cultural_context" not in payload:
                            item_title = payload.get("title", "")
                            analysis_request = CulturalAnalysisRequest(
                                title=item_title if item_title else "Untitled Item",
                                description=text
                            )
                            cultural_analysis = await cultural_service.analyze_artwork_cultural_context(analysis_request)
                            item_data["cultural_context"] = cultural_analysis.cultural_context
                        else:
                            existing = payload["cultural_context"]
                            item_data["cultural_context"] = CulturalContext(**existing) if isinstance(existing, dict) else existing
                        
                        logger.info(f"[{request_id}] Found item by scroll: {item_id}")
                        return item_data
                
                if not next_offset:
                    break
                offset = next_offset
            
            logger.warning(f"[{request_id}] Item {item_id} not found")
            return None
            
        except Exception as e:
            logger.error(f"[{request_id}] Error: {str(e)}")
            return None

    async def _get_candidate_items(self, source_item: Dict[str, Any], exclude_ids: List[str] = None, request_id: str = "") -> List[Dict[str, Any]]:
        """Get candidate items for recommendations using search infrastructure - Enhanced with logging"""
        try:
            exclude_ids = exclude_ids or []
            exclude_ids.append(source_item["id"])  # Exclude source item
            
            logger.debug(
                f"[{request_id}] Getting candidate items - "
                f"source_item_id={source_item['id']}, exclude_count={len(exclude_ids)}"
            )
            
            # Use existing search service to find similar items
            search_query = source_item["text"][:100]  # Truncate for search
            logger.debug(f"[{request_id}] Using search query: '{search_query[:50]}...'")
            
            search_start = time.time()
            search_results = search_items(
                query=search_query,
                limit=50,  # Get more candidates for filtering
                use_expansion=False,  # Skip expansion for performance
                use_reranker=False,  # Skip reranking for performance
                score_threshold=0.1  # Lower threshold for more candidates
            )
            search_time = (time.time() - search_start) * 1000
            
            logger.debug(
                f"[{request_id}] Search completed - "
                f"results_count={len(search_results)}, processing_time_ms={search_time}"
            )
            
            candidates = []
            cultural_analysis_count = 0
            
            for result in search_results:
                if result["id"] not in exclude_ids:
                    # Add cultural context
                    item_data = {
                        "id": result["id"],
                        "text": result["text"],
                        "payload": result["payload"],
                        "vector_similarity": result["score"]
                    }
                    
                    # Add cultural context if missing - FIX: Handle missing title gracefully
                    if "cultural_context" not in result["payload"]:
                        item_title = result["payload"].get("title", "")
                        
                        analysis_request = CulturalAnalysisRequest(
                            title=item_title if item_title else "Untitled Item",
                            description=result["text"]
                        )
                        cultural_analysis = await cultural_service.analyze_artwork_cultural_context(analysis_request)
                        item_data["cultural_context"] = cultural_analysis.cultural_context
                        cultural_analysis_count += 1
                    else:
                        # Handle existing cultural context
                        existing_context = result["payload"]["cultural_context"]
                        if isinstance(existing_context, dict):
                            item_data["cultural_context"] = CulturalContext(**existing_context)
                        else:
                            item_data["cultural_context"] = existing_context
                    
                    candidates.append(item_data)
            
            if cultural_analysis_count > 0:
                self.stats["cultural_analyses_performed"] += cultural_analysis_count
                logger.debug(f"[{request_id}] Performed {cultural_analysis_count} cultural analyses for candidates")
            
            logger.info(
                f"[{request_id}] Retrieved {len(candidates)} candidate items - "
                f"excluded_count={len([r for r in search_results if r['id'] in exclude_ids])}"
            )
            
            return candidates
            
        except Exception as e:
            logger.error(f"[{request_id}] Error getting candidate items: {str(e)} - error_type={type(e).__name__}")
            return []

    async def _generate_recommendations_by_type(
        self, 
        rec_type: RecommendationType, 
        source_item: Dict[str, Any], 
        candidates: List[Dict[str, Any]], 
        request: RecommendationRequest,
        request_id: str = ""
    ) -> List[RecommendationItem]:
        """Generate recommendations for a specific type - Enhanced with logging"""
        
        type_start = time.time()
        logger.debug(f"[{request_id}] Starting {rec_type.value} recommendation generation")
        
        recommendations = []
        
        try:
            if rec_type == RecommendationType.CULTURAL_SIMILARITY:
                similar_items = content_based_recommender.find_similar_items(
                    source_item, candidates, request.limit, request.similarity_threshold, request.enable_diversity, request_id
                )
                
                for item_data, similarity_result in similar_items:
                    rec_item = self._create_recommendation_item(
                        item_data, similarity_result, rec_type, SimilarityMetric.CULTURAL_CONTEXT, request_id
                    )
                    recommendations.append(rec_item)
            
            elif rec_type == RecommendationType.REGIONAL_DISCOVERY:
                regional_items = content_based_recommender.find_regional_discoveries(
                    source_item, candidates, request.limit, request_id=request_id
                )
                
                for item_data, similarity_result in regional_items:
                    rec_item = self._create_recommendation_item(
                        item_data, similarity_result, rec_type, SimilarityMetric.REGIONAL_CRAFT, request_id
                    )
                    recommendations.append(rec_item)
            
            elif rec_type == RecommendationType.FESTIVAL_SEASONAL:
                # Get current seasonal context
                seasonal_context = cultural_service.get_seasonal_context()
                current_festivals = [
                    Festival(f) for f in seasonal_context.get("active_festivals", [])
                    if f in Festival.__members__.values()
                ]
                
                seasonal_items = content_based_recommender.find_seasonal_recommendations(
                    candidates, current_festivals, request.limit, request_id
                )
                
                for item_data, similarity_result in seasonal_items:
                    rec_item = self._create_recommendation_item(
                        item_data, similarity_result, rec_type, SimilarityMetric.FESTIVAL_SEASONAL, request_id
                    )
                    recommendations.append(rec_item)
            
            processing_time = (time.time() - type_start) * 1000
            logger.debug(
                f"[{request_id}] Completed {rec_type.value} recommendation generation - "
                f"results_count={len(recommendations)}, processing_time_ms={processing_time}"
            )
        
        except Exception as e:
            logger.error(
                f"[{request_id}] Error in {rec_type.value} recommendation generation: {str(e)} - "
                f"error_type={type(e).__name__}"
            )
        
        return recommendations

    def _create_recommendation_item(
        self, 
        item_data: Dict[str, Any], 
        similarity_result, 
        rec_type: RecommendationType, 
        similarity_metric: SimilarityMetric,
        request_id: str = ""
    ) -> RecommendationItem:
        """Create a RecommendationItem from item data and similarity results - Enhanced with logging"""
        
        try:
            # Create score breakdown
            score_breakdown = RecommendationScore(
                overall_score=similarity_result.similarity_score,
                cultural_similarity=similarity_result.cultural_similarity,
                vector_similarity=similarity_result.vector_similarity,
                seasonal_relevance=similarity_result.seasonal_relevance,
                regional_match=similarity_result.regional_match,
                festival_relevance=similarity_result.festival_relevance,
                diversity_bonus=getattr(similarity_result, 'diversity_penalty', 0.0)
            )
            
            # Add seasonal context if relevant
            seasonal_context = None
            if similarity_result.seasonal_relevance > 0:
                seasonal_context = f"Seasonal relevance: {similarity_result.seasonal_relevance:.2f}"
            
            rec_item = RecommendationItem(
                id=item_data["id"],
                text=item_data["text"],
                payload=item_data["payload"],
                recommendation_type=rec_type,
                similarity_metric=similarity_metric,
                score_breakdown=score_breakdown,
                cultural_context=item_data.get("cultural_context"),
                cultural_match_reasons=similarity_result.match_reasons,
                seasonal_context=seasonal_context,
                distance_from_source=1.0 - similarity_result.vector_similarity if similarity_result.vector_similarity else None
            )
            
            logger.debug(
                f"[{request_id}] Created recommendation item - "
                f"item_id={item_data['id']}, rec_type={rec_type.value}, "
                f"overall_score={score_breakdown.overall_score}, "
                f"match_reasons_count={len(similarity_result.match_reasons)}"
            )
            
            return rec_item
            
        except Exception as e:
            logger.error(f"[{request_id}] Error creating recommendation item: {str(e)} - error_type={type(e).__name__}")
            # Return a basic recommendation item as fallback
            return RecommendationItem(
                id=item_data["id"],
                text=item_data["text"],
                payload=item_data["payload"],
                recommendation_type=rec_type,
                similarity_metric=similarity_metric,
                score_breakdown=RecommendationScore(overall_score=0.0),
                cultural_context=item_data.get("cultural_context"),
                cultural_match_reasons=[],
                seasonal_context=None
            )

    def _deduplicate_and_rank_recommendations(
        self, 
        recommendations: List[RecommendationItem], 
        limit: int,
        request_id: str = ""
    ) -> List[RecommendationItem]:
        """Deduplicate and rank recommendations - Enhanced with logging"""
        
        logger.debug(
            f"[{request_id}] Deduplicating and ranking {len(recommendations)} recommendations"
        )
        
        # Group by ID to remove duplicates
        unique_recommendations = {}
        duplicate_count = 0
        
        for rec in recommendations:
            if rec.id not in unique_recommendations:
                unique_recommendations[rec.id] = rec
            else:
                duplicate_count += 1
                # Keep the one with higher score
                if rec.score_breakdown.overall_score > unique_recommendations[rec.id].score_breakdown.overall_score:
                    unique_recommendations[rec.id] = rec
        
        if duplicate_count > 0:
            logger.debug(f"[{request_id}] Removed {duplicate_count} duplicate recommendations")
        
        # Sort by overall score
        sorted_recommendations = sorted(
            unique_recommendations.values(), 
            key=lambda x: x.score_breakdown.overall_score, 
            reverse=True
        )
        
        final_recommendations = sorted_recommendations[:limit]
        
        logger.debug(
            f"[{request_id}] Final ranking completed - "
            f"unique_count={len(unique_recommendations)}, final_count={len(final_recommendations)}, "
            f"top_score={final_recommendations[0].score_breakdown.overall_score if final_recommendations else 0.0}"
        )
        
        return final_recommendations

    def _calculate_diversity_stats(self, recommendations: List[RecommendationItem]) -> Dict[str, int]:
        """Calculate diversity statistics for recommendations - FIXED"""
        regions = set()
        craft_types = set()
        
        for rec in recommendations:
            if rec.cultural_context:
                # Safe region value extraction
                if rec.cultural_context.region:
                    if hasattr(rec.cultural_context.region, 'value'):
                        regions.add(rec.cultural_context.region.value)
                    else:
                        regions.add(str(rec.cultural_context.region))
                
                # Safe craft type value extraction
                if rec.cultural_context.craft_type:
                    if hasattr(rec.cultural_context.craft_type, 'value'):
                        craft_types.add(rec.cultural_context.craft_type.value)
                    else:
                        craft_types.add(str(rec.cultural_context.craft_type))
        
        return {
            "unique_regions": len(regions),
            "unique_craft_types": len(craft_types),
            "total_items": len(recommendations)
        }

    def _calculate_overall_confidence(self, recommendations: List[RecommendationItem]) -> float:
        """Calculate overall confidence in recommendations"""
        if not recommendations:
            return 0.0
        
        total_confidence = sum(rec.score_breakdown.overall_score for rec in recommendations)
        return total_confidence / len(recommendations)

    def _create_empty_response(self, request, message: str) -> RecommendationResponse:
        """Create empty response for error cases"""
        return RecommendationResponse(
            source_item_id=getattr(request, 'item_id', None),
            total_recommendations=0,
            recommendations=[],
            recommendation_types_used=getattr(request, 'recommendation_types', []),
            processing_time_ms=0.0
        )

    def _create_error_response(self, request, error_message: str) -> RecommendationResponse:
        """Create error response"""
        logger.error(f"Recommendation error: {error_message}")
        return self._create_empty_response(request, error_message)

    def _update_stats(self, processing_time: float):
        """Update service statistics"""
        processing_time_ms = processing_time * 1000
        self.stats["recommendations_served"] += 1
        self.stats["avg_response_time_ms"] = (
            (self.stats["avg_response_time_ms"] * (self.stats["recommendations_served"] - 1) + processing_time_ms)
            / self.stats["recommendations_served"]
        )

    # Utility methods for logging
    def _get_cultural_context_summary(self, cultural_context) -> str:
        """Get a concise summary of cultural context for logging - FIXED"""
        if not cultural_context:
            return "none"
        
        parts = []
        
        # Safe enum value extraction
        if hasattr(cultural_context, 'craft_type') and cultural_context.craft_type:
            craft_value = cultural_context.craft_type.value if hasattr(cultural_context.craft_type, 'value') else str(cultural_context.craft_type)
            parts.append(f"craft:{craft_value}")
        
        if hasattr(cultural_context, 'region') and cultural_context.region:
            region_value = cultural_context.region.value if hasattr(cultural_context.region, 'value') else str(cultural_context.region)
            parts.append(f"region:{region_value}")
        
        if hasattr(cultural_context, 'festival_relevance') and cultural_context.festival_relevance:
            parts.append(f"festivals:{len(cultural_context.festival_relevance)}")
        
        return "|".join(parts) if parts else "basic"

    def get_stats(self) -> Dict[str, Any]:
        """Get service statistics"""
        stats_data = {
            **self.stats,
            "cache_size": len(self.cache),
            "content_based_stats": content_based_recommender.get_stats()
        }
        
        logger.debug(f"Service statistics requested - {stats_data}")
        return stats_data

    def clear_cache(self):
        """Clear recommendation cache (with logging)"""
        cache_size = len(self.cache)
        self.cache.clear()
        content_based_recommender.clear_cache()
        
        logger.info(f"Recommendation service cache cleared (was {cache_size} entries)")

    async def test_item_lookup(self, item_id: str) -> Dict[str, Any]:
        """Test method to debug item lookup issues"""
        logger.info(f"Testing item lookup for: {item_id}")
        
        try:
            # Get all items and search for the ID
            all_items = []
            offset = None
            found_item = None
            
            while True:
                points, next_offset = qdrant.scroll(
                    collection_name=settings.COLLECTION_NAME,
                    limit=100,
                    offset=offset,
                    with_payload=True
                )
                
                if not points:
                    break
                
                logger.info(f"Checking batch of {len(points)} items")
                
                for point in points:
                    payload = point.payload or {}
                    point_id = str(point.id)
                    item_id_from_payload = payload.get("item_id", "")
                    
                    all_items.append({
                        "point_id": point_id,
                        "payload_item_id": item_id_from_payload,
                        "title": payload.get("title", "")[:50]
                    })
                    
                    # Check multiple ID matching strategies
                    if (point_id == item_id or 
                        item_id_from_payload == item_id or
                        item_id.lower() in payload.get("title", "").lower()):
                        found_item = {
                            "id": point_id,
                            "payload": payload,
                            "text": payload.get("text", ""),
                            "match_type": "found"
                        }
                        logger.info(f"FOUND ITEM: {point_id} matches {item_id}")
                
                offset = next_offset
                if not next_offset:
                    break
            
            return {
                "search_item_id": item_id,
                "total_items_checked": len(all_items),
                "found_item": found_item,
                "sample_items": all_items[:10],  # First 10 for debugging
                "search_suggestions": [
                    f"Try item_id: {item['point_id']}" for item in all_items[:5]
                ]
            }
            
        except Exception as e:
            logger.error(f"Error in test lookup: {str(e)}")
            return {"error": str(e)}

# Global instance
recommendation_service = CulturalRecommendationService()