# src/services/reranker_service.py - QUOTA PRESERVATION MODE
from typing import List, Dict, Any
import google.generativeai as genai
from src.config.settings import settings
import json
import re
import logging
import os

logger = logging.getLogger(__name__)

# Configure Gemini (kept for manual testing)
genai.configure(api_key=settings.GEMINI_API_KEY)

# Maximum number of candidates to send to Gemini for reranking
MAX_RERANK_CANDIDATES = 10

# QUOTA PRESERVATION - Check environment variable
DISABLE_GEMINI_RERANKING = os.getenv("DISABLE_GEMINI_RERANKING", "true").lower() == "true"


def _format_candidate(idx: int, c: Dict[str, Any]) -> str:
    """
    Create a short, human-readable string representing the candidate.
    Keep it compact to reduce token usage.
    """
    text = c.get("text") or ""
    payload = c.get("payload") or {}
    title = payload.get("title") or ""
    category = payload.get("category") or ""
    # Choose the best short snippet to describe the item
    snippet = text or title or json.dumps(payload, ensure_ascii=False)
    snippet = snippet.replace("\n", " ").strip()
    if len(snippet) > 200:
        snippet = snippet[:197] + "..."
    cat_part = f" category: {category}" if category else ""
    return f"[{idx}] {snippet}{cat_part}"


def _extract_json_from_text(s: str):
    """
    Try to robustly extract JSON from model output.
    Supports:
      - pure JSON
      - JSON wrapped in markdown/code fences
      - JSON embedded inside extra text
    Raises Exception if nothing parseable is found.
    """
    s = (s or "").strip()
    if not s:
        raise ValueError("empty response text")

    # Try pure JSON first
    try:
        return json.loads(s)
    except Exception:
        pass

    # Try code fence: ```json { ... } ```
    m = re.search(r"```(?:json)?\s*(\{[\s\S]*\}|\[[\s\S]*\])\s*```", s, flags=re.IGNORECASE)
    if m:
        try:
            return json.loads(m.group(1))
        except Exception:
            pass

    # Try to find the first JSON object/array substring
    m = re.search(r"(\{[\s\S]*\}|\[[\s\S]*\])", s)
    if m:
        try:
            return json.loads(m.group(1))
        except Exception:
            pass

    # Nothing worked
    raise ValueError("No JSON found in response")


def _cultural_score_rerank(query: str, candidates: List[Dict]) -> List[Dict]:
    """
    Enhanced fallback reranking using cultural relevance scoring.
    This preserves Gemini quota while providing intelligent reranking.
    """
    if not candidates:
        return []
    
    logger.debug(f"Using cultural relevance reranking (preserving Gemini quota): '{query}'")
    
    query_lower = query.lower()
    query_tokens = set(query_lower.split())
    
    # Cultural keywords for Indian crafts (enhanced scoring)
    cultural_keywords = {
        "high_priority": [
            "traditional", "handmade", "artisan", "heritage", "authentic", "cultural",
            "kundan", "rajasthani", "banarasi", "madhubani", "warli", "phulkari",
            "diwali", "festival", "ceremonial", "bridal", "wedding", "festive"
        ],
        "medium_priority": [
            "pottery", "ceramic", "jewelry", "textile", "silk", "brass", "wooden",
            "blue", "gold", "silver", "handcrafted", "decorative", "ornamental"
        ],
        "craft_types": [
            "pottery", "textiles", "jewelry", "woodwork", "metalcraft", "painting",
            "sculpture", "leather", "stone", "glass", "paper", "bamboo"
        ],
        "materials": [
            "clay", "ceramic", "silk", "cotton", "wool", "gold", "silver", "brass",
            "copper", "wood", "bamboo", "stone", "glass", "leather", "paper"
        ],
        "regions": [
            "rajasthan", "rajasthani", "gujarat", "punjab", "bengal", "tamil",
            "kerala", "mumbai", "delhi", "varanasi", "jaipur", "udaipur"
        ]
    }
    
    scored_candidates = []
    
    for candidate in candidates:
        text = (candidate.get("text", "") or "").lower()
        payload = candidate.get("payload", {}) or {}
        title = (payload.get("title", "") or "").lower()
        category = (payload.get("category", "") or "").lower()
        
        combined_text = f"{text} {title} {category}"
        candidate_tokens = set(combined_text.split())
        
        score = candidate.get("weighted_score", 0.0)
        cultural_bonus = 0.0
        
        # Direct query term matches (highest priority)
        query_matches = len(query_tokens & candidate_tokens)
        if query_matches > 0:
            cultural_bonus += query_matches * 0.1
        
        # High priority cultural keywords
        high_matches = sum(1 for kw in cultural_keywords["high_priority"] if kw in combined_text)
        cultural_bonus += high_matches * 0.08
        
        # Medium priority keywords  
        medium_matches = sum(1 for kw in cultural_keywords["medium_priority"] if kw in combined_text)
        cultural_bonus += medium_matches * 0.05
        
        # Craft type relevance
        craft_matches = sum(1 for kw in cultural_keywords["craft_types"] if kw in combined_text)
        cultural_bonus += craft_matches * 0.06
        
        # Material relevance
        material_matches = sum(1 for kw in cultural_keywords["materials"] if kw in combined_text)
        cultural_bonus += material_matches * 0.04
        
        # Regional relevance
        region_matches = sum(1 for kw in cultural_keywords["regions"] if kw in combined_text)
        cultural_bonus += region_matches * 0.07
        
        # Title relevance bonus (titles are more descriptive)
        if any(token in title for token in query_tokens):
            cultural_bonus += 0.1
        
        # Category exact match bonus
        if query_lower in category or category in query_lower:
            cultural_bonus += 0.15
        
        final_score = score + cultural_bonus
        
        scored_candidates.append({
            **candidate,
            "cultural_rerank_score": final_score,
            "cultural_bonus": cultural_bonus,
            "original_score": score
        })
    
    # Sort by enhanced cultural score
    reranked = sorted(scored_candidates, key=lambda x: x["cultural_rerank_score"], reverse=True)
    
    logger.debug(f"Cultural reranking applied {len(reranked)} items with cultural scoring")
    return reranked


def rerank(query: str, candidates: List[Dict]) -> List[Dict]:
    """
    Rerank candidates with quota preservation mode.
    Uses cultural relevance scoring to preserve Gemini quota for cultural analysis.
    """
    if not candidates:
        return []

    # QUOTA PRESERVATION MODE - Skip Gemini entirely
    if DISABLE_GEMINI_RERANKING:
        return _cultural_score_rerank(query, candidates)

    # Original Gemini-based reranking (only if explicitly enabled)
    logger.info(f"Using Gemini for reranking (will consume quota): '{query}'")
    
    # Limit how many candidates we send to Gemini to save tokens
    candidates_for_rerank = candidates[:MAX_RERANK_CANDIDATES]

    docs = [_format_candidate(i, c) for i, c in enumerate(candidates_for_rerank)]

    prompt = f"""
You are a ranking system. Given a search query and candidate results,
sort them by relevance to the query.

Query: "{query}"

Candidates:
{chr(10).join(docs)}

Return ONLY valid JSON in this exact format:
{{ "order": [indexes in most relevant order] }}

Example:
{{ "order": [2, 0, 1] }}
    """

    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        # Force JSON output and deterministic behavior
        response = model.generate_content(
            prompt,
            generation_config={
                "response_mime_type": "application/json",
                "temperature": 0.0,
            },
        )

        content = response.text or ""
        parsed = _extract_json_from_text(content)

        # parsed could be either a dict {"order": [...]} or an array [...]
        if isinstance(parsed, dict):
            order = parsed.get("order", [])
        elif isinstance(parsed, list):
            order = parsed
        else:
            raise ValueError("Unexpected JSON structure from reranker")

        # Normalize to integers
        order = [int(i) for i in order if str(i).isdigit()]

        # Build reranked array from indexes (indexes reference candidates_for_rerank)
        reranked_slice = [candidates_for_rerank[i] for i in order if 0 <= i < len(candidates_for_rerank)]

        # Preserve all items: append any remaining original candidates not present in reranked_slice
        reranked_ids = {c.get("id") for c in reranked_slice}
        remaining = [c for c in candidates if c.get("id") not in reranked_ids]
        final = reranked_slice + remaining
        return final[: len(candidates)]  # return same length as original list

    except Exception as e:
        logger.warning(f"Gemini reranking failed: {e}, using cultural relevance fallback")
        return _cultural_score_rerank(query, candidates)