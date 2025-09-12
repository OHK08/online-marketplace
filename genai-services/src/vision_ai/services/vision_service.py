# genai-services/src/vision_ai/services/vision_service.py
import os
import base64
from fastapi import FastAPI, UploadFile, File, HTTPException, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import google.generativeai as genai
from ..processors.image_processor import preprocess_image
from ..prompts.prompt_engineering import get_story_prompt
import logging
import jwt

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

# Authentication setup
API_KEY = os.getenv("VISION_API_KEY", "default-secret-key")  # Add to .env

def verify_api_key(x_api_key: str = Header(...)):
    if not x_api_key or x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid or missing API Key")
    return x_api_key

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
async def generate_story(image: UploadFile, x_api_key: str = Depends(verify_api_key)):
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

        # Dynamic prompt using prompt_engineering
        prompt = get_story_prompt(craft_type="pottery", language="English", tone="warm, respectful")

        # Send to Gemini
        response = model.generate_content([prompt] + image_parts)

        # Return story
        return {"story": response.text}
    except ValueError as ve:
        logger.error(f"Image processing error: {str(ve)}")
        raise HTTPException(status_code=400, detail=f"Image processing error: {str(ve)}")
    except Exception as e:
        logger.error(f"General error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing image: {str(e)}")