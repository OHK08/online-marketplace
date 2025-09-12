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

        # Step 1: Classify craft type and detect skill level
        analysis_prompt = "Analyze this craft image: identify the craft type (e.g., pottery, basket, weaving) and estimate the skill level (beginner, intermediate, expert) based on complexity. Return ONLY a JSON object with 'craft_type' and 'skill_level'."
        analysis_response = model.generate_content([analysis_prompt] + image_parts, generation_config=genai.GenerationConfig(response_mime_type="application/json"))
        analysis_text = analysis_response.text
        logger.info(f"Raw analysis: {analysis_text}")  # Log raw analysis
        try:
            analysis = json.loads(analysis_text)
            craft_type = analysis.get('craft_type', "pottery")
            skill_level = analysis.get('skill_level', "intermediate")
        except json.JSONDecodeError:
            craft_type = "pottery"
            skill_level = "intermediate"
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
            "skill_level": skill_level
        }
        return sections
    except ValueError as ve:
        logger.error(f"Image processing error: {str(ve)}")
        raise HTTPException(status_code=400, detail=f"Image processing error: {str(ve)}")
    except Exception as e:
        logger.error(f"General error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing image: {str(e)}")