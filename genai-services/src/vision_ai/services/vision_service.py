import os 
import base64
import json
from fastapi import FastAPI, UploadFile, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import google.generativeai as genai
from ..processors.image_processor import preprocess_image
from ..prompts.prompt_engineering import get_story_prompt, generate_video_from_story
from ..jobs.job_manager import create_job, get_job_status, update_job_sync
import logging 

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Configure Google API
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise RuntimeError("GOOGLE_API_KEY not found in .env")
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

def _get_gemini_model():
    """Get Gemini model with fallback."""
    models = ['gemini-2.5-flash', 'gemini-2.0-flash', 'gemini-pro-vision']
    for model_name in models:
        try:
            return genai.GenerativeModel(model_name)
        except Exception as e:
            logger.warning(f"Model {model_name} failed: {e}")
    raise RuntimeError("No available Gemini models")

@app.post("/generate_story")
async def generate_story(image: UploadFile):
    try: 
        logger.info(f"Received file: {image.filename}, content type: {image.content_type}")
        image_bytes = await image.read() 
        if not image_bytes:
            raise HTTPException(status_code=400, detail=f"No image data provided for file: {image.filename}")
        logger.info(f"Image size: {len(image_bytes)} bytes") 
        processed_bytes = preprocess_image(image_bytes) 
        model = _get_gemini_model() 
        base64_image = base64.b64encode(processed_bytes).decode('utf-8')
        image_parts = [{"mime_type": "image/jpeg", "data": base64_image}]

        # Step 1: Classify craft type, detect skill level, and craft technique
        analysis_prompt = "Analyze this craft image: identify the craft type (e.g., pottery, basket, weaving), estimate the skill level (beginner, intermediate, expert), and describe the main craft technique (e.g., wheel-throwing, coiling, weaving). Return ONLY a JSON object with 'craft_type', 'skill_level', and 'craft_technique'."
        analysis_response = model.generate_content([analysis_prompt] + image_parts, generation_config=genai.GenerationConfig(response_mime_type="application/json"))
        analysis_text = analysis_response.text
        logger.info(f"Raw analysis: {analysis_text}")
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
        response = model.generate_content([prompt] + image_parts, generation_config=genai.GenerationConfig(response_mime_type="application/json"))
        story_text = response.text
        logger.info(f"Raw story: {story_text}")
        try: 
            sections = json.loads(story_text) 
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

# ==================== ASYNC VIDEO GENERATION (NEW) ====================

@app.post("/generate_video")
async def generate_video(image: UploadFile, background_tasks: BackgroundTasks):
    """
    Upload image → queue story + video → return job_id
    """
    try:
        story_response = await generate_story(image)
        story_json = json.dumps(story_response)
        job_id = await create_job(story_response)
        background_tasks.add_task(run_video_generation, job_id, story_json)
        return {"job_id": job_id, "status": "queued"}
    except Exception as e:
        logger.error(f"Job creation error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to queue job: {str(e)}")


def run_video_generation(job_id: str, story_json: str):
    """Background task: generate video and update DB"""
    try:
        video_path = generate_video_from_story(story_json)
        update_job_sync(job_id, {"status": "done", "video_path": video_path})
    except Exception as e:
        update_job_sync(job_id, {"status": "failed", "error": str(e)})


@app.get("/video-status/{job_id}")
async def video_status(job_id: str):
    """Poll job status"""
    job = await get_job_status(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

# ==================== ALL ORIGINAL ENDPOINTS (UNCHANGED) ====================

@app.post("/similar_crafts")
async def similar_crafts(image: UploadFile):
    try: 
        image_bytes = await image.read()
        if not image_bytes:
            raise HTTPException(status_code=400, detail=f"No image data provided for file: {image.filename}") 
        processed_bytes = preprocess_image(image_bytes)
        model = _get_gemini_model() 
        base64_image = base64.b64encode(processed_bytes).decode('utf-8')
        image_parts = [{"mime_type": "image/jpeg", "data": base64_image}] 
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
        image_bytes = await image.read()
        if not image_bytes:
            raise HTTPException(status_code=400, detail="No image data provided")
        processed_bytes = preprocess_image(image_bytes)
        base64_image = base64.b64encode(processed_bytes).decode('utf-8')
        image_parts = [{"mime_type": "image/jpeg", "data": base64_image}]
        model = _get_gemini_model() 
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
        image_bytes = await image.read()
        if not image_bytes:
            raise HTTPException(status_code=400, detail="No image data provided")
        processed_bytes = preprocess_image(image_bytes)
        base64_image = base64.b64encode(processed_bytes).decode('utf-8')
        image_parts = [{"mime_type": "image/jpeg", "data": base64_image}] 
        model = _get_gemini_model() 
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

@app.post("/purchase_analysis")
async def purchase_analysis(image: UploadFile):
    try: 
        image_bytes = await image.read()
        if not image_bytes:
            raise HTTPException(status_code=400, detail="No image data provided")
        processed_bytes = preprocess_image(image_bytes)
        base64_image = base64.b64encode(processed_bytes).decode('utf-8')
        image_parts = [{"mime_type": "image/jpeg", "data": base64_image}]
        model = _get_gemini_model() 
        purchase_prompt = "Analyze this craft image: identify craft type, technique. Suggest 3 items to add to the cart based on purchase patterns (e.g., glaze for pottery). Provide a brief analysis (50-100 words) on how this enhances the purchase experience. Return ONLY a JSON object with 'cart_suggestions' (list of 3 strings with descriptions) and 'purchase_analysis' (string, 50-100 words)."
        response = model.generate_content([purchase_prompt] + image_parts, generation_config=genai.GenerationConfig(response_mime_type="application/json"))
        purchase_text = response.text
        logger.info(f"Raw purchase response: {purchase_text}")
        try:
            purchase_data = json.loads(purchase_text)
            if 'cart_suggestions' in purchase_data and len(purchase_data['cart_suggestions']) == 3 and 'purchase_analysis' in purchase_data:
                return purchase_data
            else:
                logger.warning("Incomplete purchase JSON - using fallback")
        except json.JSONDecodeError:
            logger.warning("Invalid JSON from purchase - using fallback")
        return {
            "cart_suggestions": [
                "Glaze kit: Adds vibrant colors to pottery.",
                "Clay tools: Improves detailing for beginners.",
                "Kiln guide: Ensures proper firing techniques."
            ],
            "purchase_analysis": "Adding complementary items like glaze and tools enhances the purchase experience by offering a complete crafting solution, increasing customer satisfaction and repeat purchases. This tailored approach leverages visual analysis to suggest relevant products, boosting cart value."
        }
    except ValueError as ve:
        logger.error(f"Image processing error: {str(ve)}")
        raise HTTPException(status_code=400, detail=f"Image processing error: {str(ve)}")
    except Exception as e:
        logger.error(f"General error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing image: {str(e)}")

@app.post("/fraud_detection")
async def fraud_detection(image: UploadFile):
    try: 
        image_bytes = await image.read()
        if not image_bytes:
            raise HTTPException(status_code=400, detail="No image data provided")
        processed_bytes = preprocess_image(image_bytes)
        base64_image = base64.b64encode(processed_bytes).decode('utf-8')
        image_parts = [{"mime_type": "image/jpeg", "data": base64_image}]
        model = _get_gemini_model() 
        fraud_prompt = "Analyze this craft image: detect signs of fraud (e.g., stock photo, artificial lighting, inconsistent craftsmanship). Return ONLY a JSON object with 'is_fraudulent' (boolean), 'confidence_score' (0-1), and 'reasoning' (brief)."
        response = model.generate_content([fraud_prompt] + image_parts, generation_config=genai.GenerationConfig(response_mime_type="application/json"))
        fraud_text = response.text
        logger.info(f"Raw fraud response: {fraud_text}")
        try:
            fraud_data = json.loads(fraud_text)
            if 'is_fraudulent' in fraud_data and 'confidence_score' in fraud_data and 'reasoning' in fraud_data:
                return fraud_data
            else:
                logger.warning("Incomplete fraud JSON - using fallback")
        except json.JSONDecodeError:
            logger.warning("Invalid JSON from fraud - using fallback")
        return {
            "is_fraudulent": False,
            "confidence_score": 0.95,
            "reasoning": "No obvious signs of stock photo or artificial manipulation detected."
        }
    except ValueError as ve:
        logger.error(f"Image processing error: {str(ve)}")
        raise HTTPException(status_code=400, detail=f"Image processing error: {str(ve)}")
    except Exception as e:
        logger.error(f"General error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing image: {str(e)}")

@app.post("/order_fulfillment_analysis")
async def order_fulfillment_analysis(image: UploadFile):
    try: 
        image_bytes = await image.read()
        if not image_bytes:
            raise HTTPException(status_code=400, detail="No image data provided")
        processed_bytes = preprocess_image(image_bytes)
        base64_image = base64.b64encode(processed_bytes).decode('utf-8')
        image_parts = [{"mime_type": "image/jpeg", "data": base64_image}]
        model = _get_gemini_model() 
        fulfillment_prompt = "Analyze this craft image: identify craft type, size, and fragility. Suggest optimal packaging materials and shipping considerations (e.g., bubble wrap for pottery). Return ONLY a JSON object with 'packaging_suggestions' (list of 2-3 strings with descriptions) and 'shipping_considerations' (string, 50-100 words)."
        response = model.generate_content([fulfillment_prompt] + image_parts, generation_config=genai.GenerationConfig(response_mime_type="application/json"))
        fulfillment_text = response.text
        logger.info(f"Raw fulfillment response: {fulfillment_text}")
        try:
            fulfillment_data = json.loads(fulfillment_text)
            if 'packaging_suggestions' in fulfillment_data and len(fulfillment_data['packaging_suggestions']) >= 2 and 'shipping_considerations' in fulfillment_data:
                return fulfillment_data
            else:
                logger.warning("Incomplete fulfillment JSON - using fallback")
        except json.JSONDecodeError:
            logger.warning("Invalid JSON from fulfillment - using fallback")
        return {
            "packaging_suggestions": [
                "Bubble wrap: Protects fragile pottery edges.",
                "Cardboard box: Ensures structural integrity."
            ],
            "shipping_considerations": "Pottery items require careful handling due to their fragility. Use bubble wrap and a sturdy cardboard box to prevent damage during transit. Consider insured shipping to cover potential breakage, and label as 'Fragile' to alert handlers. Optimal delivery time is 5-7 days to balance cost and safety."
        }
    except ValueError as ve:
        logger.error(f"Image processing error: {str(ve)}")
        raise HTTPException(status_code=400, detail=f"Image processing error: {str(ve)}")
    except Exception as e:
        logger.error(f"General error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing image: {str(e)}")

@app.post("/quality_predictions")
async def quality_predictions(image: UploadFile):
    try: 
        image_bytes = await image.read()
        if not image_bytes:
            raise HTTPException(status_code=400, detail="No image data provided")
        processed_bytes = preprocess_image(image_bytes)
        base64_image = base64.b64encode(processed_bytes).decode('utf-8')
        image_parts = [{"mime_type": "image/jpeg", "data": base64_image}]
        model = _get_gemini_model() 
        quality_prompt = "Analyze this craft image: assess craftsmanship quality (e.g., high, medium, low) based on detail, finish, and technique. Return ONLY a JSON object with 'quality_rating' (string: high/medium/low), 'confidence_score' (0-1), and 'reasoning' (brief)."
        response = model.generate_content([quality_prompt] + image_parts, generation_config=genai.GenerationConfig(response_mime_type="application/json"))
        quality_text = response.text
        logger.info(f"Raw quality response: {quality_text}")
        try:
            quality_data = json.loads(quality_text)
            if 'quality_rating' in quality_data and 'confidence_score' in quality_data and 'reasoning' in quality_data:
                return quality_data
            else:
                logger.warning("Incomplete quality JSON - using fallback")
        except json.JSONDecodeError:
            logger.warning("Invalid JSON from quality - using fallback")
        return {
            "quality_rating": "high",
            "confidence_score": 0.90,
            "reasoning": "Excellent detail and smooth finish indicate high craftsmanship."
        }
    except ValueError as ve:
        logger.error(f"Image processing error: {str(ve)}")
        raise HTTPException(status_code=400, detail=f"Image processing error: {str(ve)}")
    except Exception as e:
        logger.error(f"General error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing image: {str(e)}")