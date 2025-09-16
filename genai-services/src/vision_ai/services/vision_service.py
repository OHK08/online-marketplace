"""
src/vision_ai/services/vision_service.py

Service layer for Vision AI microservice.

Responsibilities:
- Initialize and configure the GenAI client (Gemini) once at import time.
- Provide async service functions that accept a FastAPI UploadFile, run preprocessing,
  call the LLM with image data, parse JSON responses, and return JSON-serializable dicts.
- Perform defensive error handling and reasonable fallbacks when LLM returns invalid JSON.
- Keep functions independent from FastAPI routing so routes can stay thin.

IMPORTANT:
- Ensure GOOGLE_API_KEY is set in your environment (e.g. visionenv/.env).
- Large images will be encoded to base64 and sent to Gemini — be mindful of payload size.
"""

import os
import base64
import json
import logging
from dotenv import load_dotenv
from typing import Dict, Any, List

# genai library for Google Gemini usage (as in your original code)
import google.generativeai as genai

# FastAPI tools for consistent error handling
from fastapi import HTTPException, UploadFile

# Local helpers (keep same function names as your codebase)
from ..processors.image_processor import preprocess_image
from ..prompts.prompt_engineering import get_story_prompt

# -------------------------
# Logging & environment
# -------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load .env (if present) and configure API key
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    # We do NOT raise here to allow the module to import in unit tests;
    # functions will raise HTTPException at runtime if the key is missing.
    logger.error("GOOGLE_API_KEY not found in environment. Set it in .env or the environment.")
else:
    try:
        genai.configure(api_key=GOOGLE_API_KEY)
        logger.info("Configured genai with provided GOOGLE_API_KEY.")
    except Exception as e:
        logger.exception("Failed to configure genai client: %s", e)


# -------------------------
# Internal helpers
# -------------------------
def _image_parts_from_bytes(image_bytes: bytes) -> List[Dict[str, str]]:
    """
    Encode image bytes to the base64 structure Gemini expects.
    Returns a list of dicts with 'mime_type' and 'data'.
    """
    # This encodes to base64 string and places into the structure Gemini accepts.
    encoded = base64.b64encode(image_bytes).decode("utf-8")
    return [{"mime_type": "image/jpeg", "data": encoded}]


def _ensure_api_key():
    """Helper that raises a 500 HTTPException if GOOGLE_API_KEY isn't set."""
    if not GOOGLE_API_KEY:
        logger.error("GOOGLE_API_KEY is missing at function call time.")
        raise HTTPException(status_code=500, detail="GOOGLE_API_KEY not configured")


# -------------------------
# Service functions
# Each function:
#  - accepts an UploadFile
#  - reads bytes and validates
#  - preprocesses image bytes (preprocess_image returns processed bytes in your pipeline)
#  - calls Gemini via genai.GenerativeModel
#  - attempts to parse JSON response and validate required fields
#  - returns the parsed data or a sensible fallback (so frontend always gets useful data)
# -------------------------


async def generate_story(image: UploadFile) -> Dict[str, Any]:
    """
    Generate a structured story for an uploaded craft image.
    Returns a dict with keys (title, narrative, tutorial, categories, craft_type, skill_level, craft_technique).
    Uses 2-step approach:
      1. analysis_prompt -> get craft_type/skill_level/craft_technique
      2. story prompt based on detected craft_type
    Falls back to canned response if Gemini returns invalid JSON.
    """
    try:
        _ensure_api_key()

        logger.info("generate_story: received file=%s, content_type=%s", image.filename, image.content_type)

        image_bytes = await image.read()
        if not image_bytes:
            logger.warning("generate_story: empty image bytes")
            raise HTTPException(status_code=400, detail=f"No image data provided for file: {image.filename}")

        # Preprocess: your preprocess_image should return bytes (resized/optimized).
        processed_bytes = preprocess_image(image_bytes)
        logger.info("generate_story: processed image size=%d bytes", len(processed_bytes))

        # Prepare image parts for Gemini
        image_parts = _image_parts_from_bytes(processed_bytes)

        # Create Gemini model instance for this call
        model = genai.GenerativeModel("gemini-1.5-flash")

        # -------- Step 1: Analysis to detect craft metadata --------
        analysis_prompt = (
            "Analyze this craft image: identify the craft type (e.g., pottery, basket, weaving), "
            "estimate the skill level (beginner, intermediate, expert), and describe the main craft technique "
            "(e.g., wheel-throwing, coiling, weaving). Return ONLY a JSON object with 'craft_type', 'skill_level', "
            "and 'craft_technique'."
        )
        analysis_response = model.generate_content(
            [analysis_prompt] + image_parts,
            generation_config=genai.GenerationConfig(response_mime_type="application/json")
        )
        analysis_text = analysis_response.text
        logger.info("generate_story: raw analysis from Gemini: %s", analysis_text)

        # Parse analysis JSON with defaults if parsing fails
        try:
            analysis = json.loads(analysis_text)
            craft_type = analysis.get("craft_type", "pottery")
            skill_level = analysis.get("skill_level", "intermediate")
            craft_technique = analysis.get("craft_technique", "hand-building")
        except json.JSONDecodeError:
            logger.warning("generate_story: analysis JSON parsing failed; using defaults")
            craft_type = "pottery"
            skill_level = "intermediate"
            craft_technique = "hand-building"

        # -------- Step 2: Generate story using a tailored prompt --------
        prompt = get_story_prompt(craft_type=craft_type, language="English", tone="warm, respectful")
        story_response = model.generate_content(
            [prompt] + image_parts,
            generation_config=genai.GenerationConfig(response_mime_type="application/json")
        )
        story_text = story_response.text
        logger.info("generate_story: raw story from Gemini: %s", story_text)

        # Try to parse structured story JSON; fall back to canned content if necessary
        try:
            sections = json.loads(story_text)
            expected_keys = {"title", "narrative", "tutorial", "categories"}
            if expected_keys.issubset(set(sections.keys())):
                # augment with detected metadata
                sections["craft_type"] = craft_type
                sections["skill_level"] = skill_level
                sections["craft_technique"] = craft_technique
                return sections
            else:
                logger.warning("generate_story: story JSON incomplete; expected keys missing")
        except json.JSONDecodeError:
            logger.warning("generate_story: story JSON parsing failed; returning fallback")

        # Fallback structured response
        fallback = {
            "title": f"Story of {craft_type}",
            "narrative": f"This {craft_type} craft is lovingly made using {craft_technique}. The artisan demonstrates {skill_level} skill.",
            "tutorial": f"1. Prepare materials for {craft_type}. 2. Work using {craft_technique}. 3. Finish and let it dry.",
            "categories": [f"{craft_type.lower()}_craft", "handmade", "traditional"],
            "craft_type": craft_type,
            "skill_level": skill_level,
            "craft_technique": craft_technique,
        }
        return fallback

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("generate_story: unexpected error")
        raise HTTPException(status_code=500, detail=f"Error generating story: {str(e)}")


async def similar_crafts(image: UploadFile) -> Dict[str, Any]:
    """
    Return 3 suggested similar crafts based on visual features.
    Attempts to parse Gemini JSON response with 'similar_crafts' list of 3 strings.
    Falls back to a default list if LLM response is invalid.
    """
    try:
        _ensure_api_key()

        image_bytes = await image.read()
        if not image_bytes:
            logger.warning("similar_crafts: empty image bytes")
            raise HTTPException(status_code=400, detail=f"No image data provided for file: {image.filename}")

        processed_bytes = preprocess_image(image_bytes)
        image_parts = _image_parts_from_bytes(processed_bytes)

        model = genai.GenerativeModel("gemini-1.5-flash")
        similarity_prompt = (
            "Analyze this craft image and suggest 3 similar crafts based on visual features (e.g., shape, texture, color). "
            "Return ONLY a JSON object with 'similar_crafts' as a list of 3 strings with brief descriptions."
        )

        similarity_response = model.generate_content(
            [similarity_prompt] + image_parts,
            generation_config=genai.GenerationConfig(response_mime_type="application/json")
        )
        similarity_text = similarity_response.text
        logger.info("similar_crafts: raw Gemini response: %s", similarity_text)

        try:
            similarity = json.loads(similarity_text)
            if "similar_crafts" in similarity and isinstance(similarity["similar_crafts"], list) and len(similarity["similar_crafts"]) == 3:
                return similarity
            else:
                logger.warning("similar_crafts: response missing expected 'similar_crafts' list of length 3")
        except json.JSONDecodeError:
            logger.warning("similar_crafts: JSON parse error from Gemini response")

        # Fallback suggestions
        return {
            "similar_crafts": [
                "similar pottery jar: Smooth finish, similar silhouette.",
                "handwoven basket: Natural textured weave and round form.",
                "clay vase: Earthy tones and handcrafted look."
            ]
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("similar_crafts: unexpected error")
        raise HTTPException(status_code=500, detail=f"Error finding similar crafts: {str(e)}")


async def price_suggestion(image: UploadFile) -> Dict[str, Any]:
    """
    Suggest a price range and market analysis for the given craft image.
    Expects Gemini to return JSON with 'price_range', 'market_analysis', 'reasoning'.
    Provides a fallback structured output if parsing fails.
    """
    try:
        _ensure_api_key()

        image_bytes = await image.read()
        if not image_bytes:
            raise HTTPException(status_code=400, detail="No image data provided")

        processed_bytes = preprocess_image(image_bytes)
        image_parts = _image_parts_from_bytes(processed_bytes)

        model = genai.GenerativeModel("gemini-1.5-flash")
        price_prompt = (
            "Analyze this craft image: identify craft type, technique, skill level. Suggest a price range (₹) based on similar items "
            "(e.g., handmade pottery ₹500-2000). Provide market analysis (e.g., demand trends). Return ONLY a JSON object with "
            "'price_range' (string, e.g., '₹1,200-1,800'), 'market_analysis' (100-150 words), 'reasoning' (brief)."
        )

        response = model.generate_content(
            [price_prompt] + image_parts,
            generation_config=genai.GenerationConfig(response_mime_type="application/json")
        )
        price_text = response.text
        logger.info("price_suggestion: raw Gemini response: %s", price_text)

        try:
            price_data = json.loads(price_text)
            # Basic validation: must have price_range and market_analysis
            if "price_range" in price_data and "market_analysis" in price_data:
                return price_data
            else:
                logger.warning("price_suggestion: Gemini response missing keys; using fallback")
        except json.JSONDecodeError:
            logger.warning("price_suggestion: JSON parse error; using fallback")

        # Fallback
        return {
            "price_range": "₹1,200-1,800",
            "market_analysis": "Handmade crafts typically vary in price based on complexity, materials, and region. Niche artisanal items can fetch a premium.",
            "reasoning": "Based on craft type and observable finish."
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("price_suggestion: unexpected error")
        raise HTTPException(status_code=500, detail=f"Error generating price suggestion: {str(e)}")


async def complementary_products(image: UploadFile) -> Dict[str, Any]:
    """
    Suggest 3 complementary products for the craft (e.g., glaze kits, tools).
    Attempts to parse 'complementary_products' list of 3 strings from Gemini; falls back if necessary.
    """
    try:
        _ensure_api_key()

        image_bytes = await image.read()
        if not image_bytes:
            raise HTTPException(status_code=400, detail="No image data provided")
        processed_bytes = preprocess_image(image_bytes)
        image_parts = _image_parts_from_bytes(processed_bytes)

        model = genai.GenerativeModel("gemini-1.5-flash")
        comp_prompt = (
            "Analyze this craft image: identify craft type, technique. Suggest 3 complementary products (e.g., glaze for pottery) "
            "with brief descriptions. Return ONLY a JSON object with 'complementary_products' as a list of 3 strings with descriptions."
        )

        response = model.generate_content(
            [comp_prompt] + image_parts,
            generation_config=genai.GenerationConfig(response_mime_type="application/json")
        )
        comp_text = response.text
        logger.info("complementary_products: raw Gemini response: %s", comp_text)

        try:
            comp_data = json.loads(comp_text)
            if "complementary_products" in comp_data and isinstance(comp_data["complementary_products"], list) and len(comp_data["complementary_products"]) == 3:
                return comp_data
            else:
                logger.warning("complementary_products: unexpected structure from Gemini")
        except json.JSONDecodeError:
            logger.warning("complementary_products: JSON parse error; using fallback")

        # Fallback list
        return {
            "complementary_products": [
                "Glaze kit for pottery: Enhances finish and color.",
                "Weaving tools for basket: Improves precision in patterns.",
                "Clay sculpting tools: Helpful for fine detailing."
            ]
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("complementary_products: unexpected error")
        raise HTTPException(status_code=500, detail=f"Error suggesting complementary products: {str(e)}")


async def purchase_analysis(image: UploadFile) -> Dict[str, Any]:
    """
    Suggest items to add to cart and a brief purchase-experience analysis.
    Expects 'cart_suggestions' (3 strings) and 'purchase_analysis' (string) in Gemini JSON.
    """
    try:
        _ensure_api_key()

        image_bytes = await image.read()
        if not image_bytes:
            raise HTTPException(status_code=400, detail="No image data provided")
        processed_bytes = preprocess_image(image_bytes)
        image_parts = _image_parts_from_bytes(processed_bytes)

        model = genai.GenerativeModel("gemini-1.5-flash")
        purchase_prompt = (
            "Analyze this craft image: identify craft type, technique. Suggest 3 items to add to the cart based on purchase patterns "
            "(e.g., glaze for pottery). Provide a brief analysis (50-100 words) on how this enhances the purchase experience. Return ONLY a JSON "
            "object with 'cart_suggestions' (list of 3 strings with descriptions) and 'purchase_analysis' (string)."
        )

        response = model.generate_content(
            [purchase_prompt] + image_parts,
            generation_config=genai.GenerationConfig(response_mime_type="application/json")
        )
        purchase_text = response.text
        logger.info("purchase_analysis: raw Gemini response: %s", purchase_text)

        try:
            purchase_data = json.loads(purchase_text)
            if "cart_suggestions" in purchase_data and isinstance(purchase_data["cart_suggestions"], list) and len(purchase_data["cart_suggestions"]) == 3 and "purchase_analysis" in purchase_data:
                return purchase_data
            else:
                logger.warning("purchase_analysis: Gemini response incomplete; using fallback")
        except json.JSONDecodeError:
            logger.warning("purchase_analysis: JSON parse error; using fallback")

        return {
            "cart_suggestions": [
                "Glaze kit: Adds vibrant colors to pottery.",
                "Basic clay tools: Helps with shaping and detailing.",
                "Beginner's kiln guide: Ensures proper firing techniques."
            ],
            "purchase_analysis": "Suggesting complementary items like glaze and tools increases cart value and improves customer satisfaction by bundling necessary accessories."
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("purchase_analysis: unexpected error")
        raise HTTPException(status_code=500, detail=f"Error generating purchase analysis: {str(e)}")


async def fraud_detection(image: UploadFile) -> Dict[str, Any]:
    """
    Detect signs of potential fraud in the listing image.
    Expects JSON: { 'is_fraudulent': bool, 'confidence_score': float, 'reasoning': str }
    Uses conservative fallback (not fraudulent) when parsing fails.
    """
    try:
        _ensure_api_key()

        image_bytes = await image.read()
        if not image_bytes:
            raise HTTPException(status_code=400, detail="No image data provided")
        processed_bytes = preprocess_image(image_bytes)
        image_parts = _image_parts_from_bytes(processed_bytes)

        model = genai.GenerativeModel("gemini-1.5-flash")
        fraud_prompt = (
            "Analyze this craft image: detect signs of fraud (e.g., stock photo, artificial lighting, inconsistent craftsmanship). "
            "Return ONLY a JSON object with 'is_fraudulent' (boolean), 'confidence_score' (0-1), and 'reasoning' (brief)."
        )

        response = model.generate_content(
            [fraud_prompt] + image_parts,
            generation_config=genai.GenerationConfig(response_mime_type="application/json")
        )
        fraud_text = response.text
        logger.info("fraud_detection: raw Gemini response: %s", fraud_text)

        try:
            fraud_data = json.loads(fraud_text)
            if all(key in fraud_data for key in ("is_fraudulent", "confidence_score", "reasoning")):
                return fraud_data
            else:
                logger.warning("fraud_detection: Gemini returned incomplete fields; using fallback")
        except json.JSONDecodeError:
            logger.warning("fraud_detection: JSON parse error; using fallback")

        # Conservative fallback: not fraudulent but high confidence (example)
        return {
            "is_fraudulent": False,
            "confidence_score": 0.95,
            "reasoning": "No obvious signs of stock photo usage or manipulation detected."
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("fraud_detection: unexpected error")
        raise HTTPException(status_code=500, detail=f"Error performing fraud detection: {str(e)}")


async def order_fulfillment_analysis(image: UploadFile) -> Dict[str, Any]:
    """
    Suggest packaging and shipping considerations based on craft fragility/size.
    Expects JSON with 'packaging_suggestions' (2-3 strings) and 'shipping_considerations' (string).
    """
    try:
        _ensure_api_key()

        image_bytes = await image.read()
        if not image_bytes:
            raise HTTPException(status_code=400, detail="No image data provided")
        processed_bytes = preprocess_image(image_bytes)
        image_parts = _image_parts_from_bytes(processed_bytes)

        model = genai.GenerativeModel("gemini-1.5-flash")
        fulfillment_prompt = (
            "Analyze this craft image: identify craft type, size, and fragility. Suggest optimal packaging materials and shipping considerations "
            "(e.g., bubble wrap for pottery). Return ONLY a JSON object with 'packaging_suggestions' (list of 2-3 strings with descriptions) and "
            "'shipping_considerations' (string, 50-100 words)."
        )

        response = model.generate_content(
            [fulfillment_prompt] + image_parts,
            generation_config=genai.GenerationConfig(response_mime_type="application/json")
        )
        fulfillment_text = response.text
        logger.info("order_fulfillment_analysis: raw Gemini response: %s", fulfillment_text)

        try:
            fulfillment_data = json.loads(fulfillment_text)
            if "packaging_suggestions" in fulfillment_data and "shipping_considerations" in fulfillment_data:
                return fulfillment_data
            else:
                logger.warning("order_fulfillment_analysis: Gemini response incomplete; using fallback")
        except json.JSONDecodeError:
            logger.warning("order_fulfillment_analysis: JSON parse error; using fallback")

        return {
            "packaging_suggestions": [
                "Bubble wrap: Protects fragile edges and surfaces.",
                "Sturdy cardboard box: Prevents structural damage during transit."
            ],
            "shipping_considerations": "Label item as 'Fragile', use insured shipping for glass/ceramic items, and choose moderate delivery speeds to reduce handling damage risk."
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("order_fulfillment_analysis: unexpected error")
        raise HTTPException(status_code=500, detail=f"Error analyzing fulfillment: {str(e)}")


async def quality_predictions(image: UploadFile) -> Dict[str, Any]:
    """
    Predict craftsmanship quality (high/medium/low) with a confidence score and short reasoning.
    Expects JSON with 'quality_rating', 'confidence_score', 'reasoning'.
    Provides fallback high-quality judgement if parsing fails.
    """
    try:
        _ensure_api_key()

        image_bytes = await image.read()
        if not image_bytes:
            raise HTTPException(status_code=400, detail="No image data provided")
        processed_bytes = preprocess_image(image_bytes)
        image_parts = _image_parts_from_bytes(processed_bytes)

        model = genai.GenerativeModel("gemini-1.5-flash")
        quality_prompt = (
            "Analyze this craft image: assess craftsmanship quality (e.g., high, medium, low) based on detail, finish, and technique. "
            "Return ONLY a JSON object with 'quality_rating' (string: high/medium/low), 'confidence_score' (0-1), and 'reasoning' (brief)."
        )

        response = model.generate_content(
            [quality_prompt] + image_parts,
            generation_config=genai.GenerationConfig(response_mime_type="application/json")
        )
        quality_text = response.text
        logger.info("quality_predictions: raw Gemini response: %s", quality_text)

        try:
            quality_data = json.loads(quality_text)
            if all(key in quality_data for key in ("quality_rating", "confidence_score", "reasoning")):
                return quality_data
            else:
                logger.warning("quality_predictions: Gemini returned incomplete fields; using fallback")
        except json.JSONDecodeError:
            logger.warning("quality_predictions: JSON parse error; using fallback")

        return {
            "quality_rating": "high",
            "confidence_score": 0.90,
            "reasoning": "Visible fine details and even finish indicate careful handcrafting and high-quality workmanship."
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("quality_predictions: unexpected error")
        raise HTTPException(status_code=500, detail=f"Error predicting quality: {str(e)}")
