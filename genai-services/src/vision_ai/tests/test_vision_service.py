import os
import base64  # Added import
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import google.generativeai as genai
from .image_processor import preprocess_image  # Import from your file

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
async def generate_story(image: Annotated[UploadFile, File(description="Upload an image of the artisan craft")]):
    try:
        # Read and preprocess image
        image_bytes = await image.read()
        processed_bytes = preprocess_image(image_bytes)

        # Configure Gemini model
        model = genai.GenerativeModel('gemini-1.5-flash')

        # Convert to base64 for Gemini
        base64_image = base64.b64encode(processed_bytes).decode('utf-8')
        image_parts = [{"mime_type": "image/jpeg", "data": base64_image}]

        # Simple prompt for Day 1
        prompt = "Describe this artisan craft image in simple terms, focusing on the craft type and visual details."

        # Send to Gemini
        response = model.generate_content([prompt] + image_parts)

        # Return description
        return {"description": response.text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing image: {str(e)}")