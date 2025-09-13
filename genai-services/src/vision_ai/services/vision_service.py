# genai-services/src/vision_ai/services/vision_service.py
import os
import base64
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import google.generativeai as genai
from ..processors.image_processor import preprocess_image
from ..prompts.prompt_engineering import get_story_prompt
import logging
import json

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Configure Google API
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise RuntimeError("❌ GOOGLE_API_KEY not found in .env")
genai.configure(api_key=GOOGLE_API_KEY)

# FastAPI app setup
app = FastAPI(title="Vision AI Service")

# Allow cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/generate_story")
async def generate_story(image: UploadFile):
    try:
        # Log filename
        logger.info(f"Received file: {image.filename}, content type: {image.content_type}")

        # Read image
        image_bytes = await image.read()
        if not image_bytes:
            raise HTTPException(status_code=400, detail=f"No image data provided for file: {image.filename}")

        # Log image size
        logger.info(f"Image size: {len(image_bytes)} bytes")

        # Preprocess image
        processed_bytes = preprocess_image(image_bytes)

        # Configure Gemini model
        model = genai.GenerativeModel('gemini-1.5-flash')

        # Convert to base64 for Gemini
        base64_image = base64.b64encode(processed_bytes).decode('utf-8')
        image_parts = [{"mime_type": "image/jpeg", "data": base64_image}]

        # Step 1: Classify craft type, detect skill level, and craft technique
        analysis_prompt = "Analyze this craft image: identify the craft type (e.g., pottery, basket, weaving), estimate the skill level (beginner, intermediate, expert), and describe the main craft technique (e.g., wheel-throwing, coiling, weaving). Return ONLY a JSON object with 'craft_type', 'skill_level', and 'craft_technique'."
        analysis_response = model.generate_content([analysis_prompt] + image_parts, generation_config=genai.GenerationConfig(response_mime_type="application/json"))
        analysis_text = analysis_response.text
        logger.info(f"Raw analysis: {analysis_text}")  # Log raw analysis
        try:
            analysis = json.loads(analysis_text)
            craft_type = analysis.get('craft_type', "pottery")
            skill_level = analysis.get('skill_level', "intermediate")
            craft_technique = analysis.get('craft_technique', "hand-building")
        except json.JSONDecodeError:
            craft_type = "pottery"
            skill_level = "intermediate"
            craft_technique = "hand-building"
            logger.warning("Invalid JSON from analysis - using defaults")

        # Dynamic prompt with detected craft type
        prompt = get_story_prompt(craft_type=craft_type, language="English", tone="warm, respectful")

        # Send to Gemini with JSON config
        response = model.generate_content([prompt] + image_parts, generation_config=genai.GenerationConfig(response_mime_type="application/json"))
        story_text = response.text
        logger.info(f"Raw story: {story_text}")  # Log raw story
        try:
            sections = json.loads(story_text)
            # Check completeness
            if all(key in sections for key in ['title', 'narrative', 'tutorial', 'categories']):
                sections['craft_type'] = craft_type
                sections['skill_level'] = skill_level
                sections['craft_technique'] = craft_technique
                return sections
            else:
                logger.warning("Incomplete JSON from Gemini - using fallback")
        except json.JSONDecodeError:
            logger.warning("Invalid JSON from Gemini - using fallback")
        # Fallback if JSON fails
        sections = {
            "title": f"Story of {craft_type}",
            "narrative": f"This {craft_type} craft is made with skill. The artisan uses traditional methods to create beautiful pieces.",
            "tutorial": f"1. Prepare materials for {craft_type}. 2. Shape and build. 3. Finish and dry.",
            "categories": [f"{craft_type.lower()}_craft", "handmade", "traditional"],
            "craft_type": craft_type,
            "skill_level": skill_level,
            "craft_technique": craft_technique
        }
        return sections

    except ValueError as ve:
        logger.error(f"Image processing error: {str(ve)}")
        raise HTTPException(status_code=400, detail=f"Image processing error: {str(ve)}")
    except Exception as e:
        logger.error(f"General error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing image: {str(e)}")

@app.post("/similar_crafts")
async def similar_crafts(image: UploadFile):
    try:
        # Read image
        image_bytes = await image.read()
        if not image_bytes:
            raise HTTPException(status_code=400, detail=f"No image data provided for file: {image.filename}")

        # Preprocess image
        processed_bytes = preprocess_image(image_bytes)

        # Configure Gemini model
        model = genai.GenerativeModel('gemini-1.5-flash')

        # Convert to base64 for Gemini
        base64_image = base64.b64encode(processed_bytes).decode('utf-8')
        image_parts = [{"mime_type": "image/jpeg", "data": base64_image}]

        # Analyze for similarity features
        similarity_prompt = "Analyze this craft image and suggest 3 similar crafts based on visual features (e.g., shape, texture, color). Return ONLY a JSON object with 'similar_crafts' as a list of 3 strings with brief descriptions."
        similarity_response = model.generate_content([similarity_prompt] + image_parts, generation_config=genai.GenerationConfig(response_mime_type="application/json"))
        similarity_text = similarity_response.text
        logger.info(f"Raw similarity: {similarity_text}")
        try:
            similarity = json.loads(similarity_text)
            if 'similar_crafts' in similarity and len(similarity['similar_crafts']) == 3:
                return similarity
            else:
                logger.warning("Incomplete similarity JSON - using fallback")
        except json.JSONDecodeError:
            logger.warning("Invalid JSON from similarity - using fallback")
        return {
            "similar_crafts": [
                "similar pottery jar: Smooth finish, similar shape.",
                "handwoven basket: Natural texture, round design.",
                "clay vase: Earthy tones, handcrafted look."
            ]
        }

    except ValueError as ve:
        logger.error(f"Image processing error: {str(ve)}")
        raise HTTPException(status_code=400, detail=f"Image processing error: {str(ve)}")
    except Exception as e:
        logger.error(f"General error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing image: {str(e)}")

@app.post("/price_suggestion")
async def price_suggestion(image: UploadFile):
    try:
        # Read and preprocess image
        image_bytes = await image.read()
        if not image_bytes:
            raise HTTPException(status_code=400, detail="No image data provided")
        processed_bytes = preprocess_image(image_bytes)
        base64_image = base64.b64encode(processed_bytes).decode('utf-8')
        image_parts = [{"mime_type": "image/jpeg", "data": base64_image}]

        # Configure Gemini
        model = genai.GenerativeModel('gemini-1.5-flash')

        # Prompt for price suggestion and market analysis
        price_prompt = "Analyze this craft image: identify craft type, technique, skill level. Suggest a price range (₹) based on similar items (e.g., handmade pottery ₹500-2000). Provide market analysis (e.g., demand trends). Return ONLY a JSON object with 'price_range' (string, e.g., '₹1,200-1,800'), 'market_analysis' (100-150 words), 'reasoning' (brief)."
        response = model.generate_content([price_prompt] + image_parts, generation_config=genai.GenerationConfig(response_mime_type="application/json"))
        price_text = response.text
        logger.info(f"Raw price response: {price_text}")
        try:
            price_data = json.loads(price_text)
            return price_data
        except json.JSONDecodeError:
            return {
                "price_range": "₹1,200-1,800",
                "market_analysis": "Handmade pottery is in high demand due to cultural trends, with prices varying by technique and skill level.",
                "reasoning": "Based on craft type and quality."
            }
    except ValueError as ve:
        logger.error(f"Image processing error: {str(ve)}")
        raise HTTPException(status_code=400, detail=f"Image processing error: {str(ve)}")
    except Exception as e:
        logger.error(f"General error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing image: {str(e)}")

@app.post("/complementary_products")
async def complementary_products(image: UploadFile):
    try:
        # Read and preprocess image
        image_bytes = await image.read()
        if not image_bytes:
            raise HTTPException(status_code=400, detail="No image data provided")
        processed_bytes = preprocess_image(image_bytes)
        base64_image = base64.b64encode(processed_bytes).decode('utf-8')
        image_parts = [{"mime_type": "image/jpeg", "data": base64_image}]

        # Configure Gemini
        model = genai.GenerativeModel('gemini-1.5-flash')

        # Prompt for complementary analysis
        comp_prompt = "Analyze this craft image: identify craft type, technique. Suggest 3 complementary products (e.g., glaze for pottery) with brief descriptions. Return ONLY a JSON object with 'complementary_products' as a list of 3 strings with descriptions."
        response = model.generate_content([comp_prompt] + image_parts, generation_config=genai.GenerationConfig(response_mime_type="application/json"))
        comp_text = response.text
        logger.info(f"Raw complementary response: {comp_text}")
        try:
            comp_data = json.loads(comp_text)
            if 'complementary_products' in comp_data and len(comp_data['complementary_products']) == 3:
                return comp_data
            else:
                logger.warning("Incomplete complementary JSON - using fallback")
        except json.JSONDecodeError:
            logger.warning("Invalid JSON from complementary - using fallback")
        return {
            "complementary_products": [
                "Glaze kit for pottery: Enhances finish and color.",
                "Weaving tools for basket: Improves precision in patterns.",
                "Clay tools for hand-building: Essential for shaping details."
            ]
        }
    except ValueError as ve:
        logger.error(f"Image processing error: {str(ve)}")
        raise HTTPException(status_code=400, detail=f"Image processing error: {str(ve)}")
    except Exception as e:
        logger.error(f"General error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing image: {str(e)}")