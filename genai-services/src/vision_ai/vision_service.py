import os
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import google.generativeai as genai
from PIL import Image
import io
from typing import Annotated
# from fastapi import FastAPI, UploadFile, File


# Load environment variables
load_dotenv()

# Configure Google API
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise RuntimeError("❌ GOOGLE_API_KEY not found in .env")

genai.configure(api_key=GOOGLE_API_KEY)

# FastAPI app setup
app = FastAPI(title="Vision AI Service")

# Allow cross-origin requests (optional if frontend will call this API)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
@app.post("/generate_story")
async def generate_story(image: Annotated[UploadFile, File(description="Upload an image of the artisan craft")]):
    # Read and preprocess image
    image_bytes = await image.read()
    processed_bytes = preprocess_image(image_bytes)
    
    # Base64 encode the image
    base64_image = base64.b64encode(processed_bytes).decode('utf-8')
    
    # Configure Google Generative AI with API key
    genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
    
    # Prepare the image data
    image_parts = [
        {
            "mime_type": "image/jpeg",
            "data": base64_image
        }
    ]
    
    # Mock response for Day 2 (to be replaced with API call later)
    return {
        "title": "Mock Title: Processed Artisan Craft",
        "narrative": "This is a mock narrative generated after processing the image.",
        "tutorial": "Step 1: Mock step after processing. Step 2: Another mock step."
    }
def preprocess_image(image_bytes: bytes) -> bytes:
    # Open and validate image
    img = Image.open(io.BytesIO(image_bytes))
    if img.format not in ["JPEG", "PNG"]:
        raise ValueError("Unsupported image format")
    
    # Resize to 512x512 for consistency
    img = img.convert("RGB").resize((512, 512), Image.Resampling.LANCZOS)
    
    # Save back to bytes
    buffered = io.BytesIO()
    img.save(buffered, format="JPEG")
    return buffered.getvalue()