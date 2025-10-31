# ==============================================
# YOUR ORIGINAL CODE — 100% UNTOUCHED
# ==============================================

def get_story_prompt(craft_type: str, language: str, tone: str) -> str: 
    # Craft-specific guidance 
    craft_guidelines = {
        "pottery": "Emphasize wheel-throwing or hand-building techniques, clay types, firing processes, and cultural context (e.g., regional traditions).",
        "basket": "Focus on weaving patterns, natural fibers, traditional craftsmanship, and cultural significance.",
        "weaving": "Highlight loom techniques, thread types, cultural patterns, and historical use."
    }
    guideline = craft_guidelines.get(craft_type, "Describe the craft's unique techniques, materials, and cultural context in detail.")
    
    # Style consistency template
    style_template = f"Maintain a consistent {tone} tone throughout, using vivid, respectful language about artisans, including cultural details to enhance engagement and authenticity."
    
    # Explicit section requirements with examples
    section_example = """
    Example format:
    {
        "title": "Handmade Clay Pot of Timeless Craft",
        "narrative": "Originating from ancient villages, this pot is crafted using local clay by artisans honoring a 500-year tradition... (150-200 words)",
        "tutorial": "1. Prepare clay from local soil. 2. Shape on wheel with steady hands. 3. Fire in a wood kiln... (50-100 words, 3-5 steps)",
        "categories": ["pottery", "handmade", "traditional", "cultural heritage"]
    }
    """
    
    base_prompt = f"Create a detailed, culturally rich story about this {craft_type} craft image. {guideline} {style_template} {section_example} Return ONLY a JSON object with these keys: 'title' (5-10 words), 'narrative' (150-200 words about its creation with cultural context), 'tutorial' (50-100 words with 3-5 clear, culturally informed steps), 'categories' (list of 3-5 relevant categories including cultural aspects). Use {language} and ensure all keys are present with high quality or regenerate."
    return base_prompt 


# ==================== NEW METHODS BELOW ====================

from typing import Dict, Any
import json


def story_to_video_prompt(story_json: str) -> str:
    """
    Convert story JSON (from Gemini) into a Veo video prompt.
    Input: JSON string with 'narrative' field
    Output: Short, vivid, 5-second animation prompt
    """
    try:
        story_data = json.loads(story_json)
    except json.JSONDecodeError:
        # Fallback if not valid JSON
        story_data = {"narrative": story_json}

    narrative = story_data.get("narrative", "")[:300]  # First 300 chars
    title = story_data.get("title", "Craft Story")[:50]

    # Extract key action + setting
    action_keywords = ["weaves", "shapes", "fires", "throws", "builds", "paints", "carves"]
    setting_keywords = ["village", "river", "mountain", "forest", "market", "home"]

    action = next((word for word in action_keywords if word in narrative.lower()), "crafts")
    setting = next((word for word in setting_keywords if word in narrative.lower()), "workshop")

    # Build Veo prompt
    video_prompt = (
        f"Animated {action} scene: {title}. "
        f"{narrative.split('.')[0]}. "
        f"In {setting}, warm lighting, smooth motion, cartoon style, 5 seconds."
    )
    return video_prompt.strip()


def _generate_veo_video(self, prompt: str) -> Path:
    try:
        from google.cloud.aiplatform import PredictionServiceClient
        from google.cloud.aiplatform_v1.types import PredictRequest
        import time

        # Publisher model endpoint
        endpoint = f"projects/{self.project_id}/locations/{self.location}/publishers/google/models/veo-3.1-generate-preview"
        
        client = PredictionServiceClient()
        request = PredictRequest(
            endpoint=endpoint,
            instances=[{"prompt": prompt}],
            parameters={
                "duration": 8,
                "aspect_ratio": "16:9",
                "fps": 24,
                "resolution": "1080p",
                "storageUri": f"gs://{self.bucket_name}/outputs/"  # GCS output
            }
        )

        # Call predictLongRunning
        response = client.predict_long_running(request=request)
        operation = response.operation

        # Poll LRO (30–120s)
        print("V E O LRO started — polling...")
        while not operation.done():
            time.sleep(10)
            operation = client.get_operation(operation.name)
            print("Polling...")

        # Get output
        result = operation.result()
        video_uri = result.predictions[0]['videoUri']  # GCS URI
        print(f"V E O video: {video_uri}")

        # Download
        video_path = self.output_dir / f"veo_{uuid.uuid4().hex}.mp4"
        storage_client = storage.Client(project=self.project_id)
        bucket = storage_client.bucket(self.bucket_name)
        blob_name = video_uri.split('/')[-1]
        blob = bucket.blob(blob_name)
        blob.download_to_filename(str(video_path))
        
        return video_path

    except Exception as e:
        logger.error(f"V E O failed: {e}")
        return self._create_mock_video(prompt)
# src/vision_ai/prompts/prompt_engineering.py

def story_to_veo_prompt(story_json: str) -> str:
    story = json.loads(story_json)
    narrative = story['narrative'][:300]
    return f"8s cinematic animation of {story['craft_type']}: {narrative}. Traditional Indian style, smooth motion, 1080p."


# ==============================================
# NEW ADDITION — SAFE, NO OVERWRITE
# ==============================================

def story_to_veo_prompt_v2(story_json: str) -> str:
    """
    V E O 3.1 Optimized — 8s, 1080p, Cultural, Cinematic
    Uses full story context, craft_type, and narrative
    """
    try:
        story = json.loads(story_json)
    except json.JSONDecodeError:
        story = {"narrative": story_json, "craft_type": "craft", "title": "Craft Story"}

    narrative = story.get("narrative", "")[:350]
    craft = story.get("craft_type", "craft")
    title = story.get("title", "Traditional Craft")[:60]

    return f"""
    8-second cinematic animation of {craft.lower()} craft: "{title}".
    {narrative}
    Traditional Indian miniature painting style brought to life.
    Artisan hands shaping with precision, warm golden lighting, smooth fluid motion.
    Cultural details: regional patterns, clay dust in air, glowing kiln in background.
    Vibrant colors, intricate textures, emotional storytelling.
    1080p, 24 FPS, 16:9 aspect ratio. No text overlays. Natural cinematic flow.
    """.strip()
