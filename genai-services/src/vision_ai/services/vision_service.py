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
        analysis_prompt = "Analyze this craft image: identify the craft type (e.g., pottery, basket, weaving) and estimate the skill level (beginner, intermediate, expert) based on complexity. Return as 'Craft type: [type]' and 'Skill level: [level]' on separate lines."
        analysis_response = model.generate_content([analysis_prompt] + image_parts)
        analysis_text = analysis_response.text
        logger.info(f"Raw analysis: {analysis_text}")  # Log raw analysis
        craft_type = "unknown"
        skill_level = "unknown"
        for line in analysis_text.split('\n'):
            line = line.strip().lower()
            if line.startswith("craft type:"):
                craft_type = line.replace("craft type:", "").strip()
            elif line.startswith("skill level:"):
                skill_level = line.replace("skill level:", "").strip()
        if not craft_type:
            craft_type = "pottery"  # Default if analysis fails
            skill_level = "intermediate"

        # Dynamic prompt with detected craft type
        prompt = get_story_prompt(craft_type=craft_type, language="English", tone="warm, respectful")

        # Send to Gemini with retry logic
        max_retries = 2
        for attempt in range(max_retries):
            response = model.generate_content([prompt] + image_parts)
            story_text = response.text
            logger.info(f"Raw story (attempt {attempt + 1}): {story_text}")  # Log raw story
            sections = {"title": "", "narrative": "", "tutorial": "", "categories": []}
            current_section = None
            lines = story_text.split('\n')
            i = 0
            while i < len(lines):
                line = lines[i].strip()
                if line.startswith('# Title'):
                    sections['title'] = line.replace('# Title', '').replace(':', '').strip() or f"Story of {craft_type}"
                    i += 1
                    while i < len(lines) and not lines[i].strip().startswith('#'):
                        sections['title'] += ' ' + lines[i].strip()
                        i += 1
                elif line.startswith('# Narrative'):
                    current_section = 'narrative'
                    sections['narrative'] = line.replace('# Narrative', '').replace(':', '').strip() or f"This {craft_type} is crafted with care by artisans."
                    i += 1
                    while i < len(lines) and not lines[i].strip().startswith('#'):
                        sections['narrative'] += ' ' + lines[i].strip()
                        i += 1
                elif line.startswith('# Tutorial'):
                    current_section = 'tutorial'
                    sections['tutorial'] = line.replace('# Tutorial', '').replace(':', '').strip() or f"1. Gather {craft_type} materials. 2. Craft with care. 3. Finish the piece."
                    i += 1
                    while i < len(lines) and not lines[i].strip().startswith('#'):
                        sections['tutorial'] += ' ' + lines[i].strip()
                        i += 1
                elif line.startswith('# Categories'):
                    sections['categories'] = [cat.strip() for cat in line.replace('# Categories', '').replace(':', '').strip().split(',') if cat.strip()] or [f"{craft_type.lower()}_craft", "handmade", "traditional"]
                    i += 1
                else:
                    i += 1

            # Minimal check
            if sections['title'] and sections['narrative'] and sections['tutorial'] and sections['categories']:
                logger.info(f"Success on attempt {attempt + 1}: {sections}")
                break
            logger.warning(f"Attempt {attempt + 1} failed: Incomplete story. Sections: {sections}")
        else:
            logger.error("All retries failed - using minimal fallback")
            sections = {
                "title": f"Minimal {craft_type} Story",
                "narrative": f"This {craft_type} craft reflects traditional techniques. Details unavailable due to image issues.",
                "tutorial": f"1. Prepare {craft_type} materials. 2. Craft with care. 3. Complete.",
                "categories": [f"{craft_type.lower()}_craft", "handmade", "traditional"]
            }

        # Add classification and skill level
        sections["craft_type"] = craft_type
        sections["skill_level"] = skill_level

        return sections
    except ValueError as ve:
        logger.error(f"Image processing error: {str(ve)}")
        raise HTTPException(status_code=400, detail=f"Image processing error: {str(ve)}")
    except Exception as e:
        logger.error(f"General error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing image: {str(e)}")