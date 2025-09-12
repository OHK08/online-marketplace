# genai-services/src/vision_ai/prompts/prompt_engineering.py
def get_story_prompt(craft_type: str, language: str, tone: str) -> str:
    base_prompt = f"Create a short mock story about this {craft_type} craft image. Include a title (5-10 words) and a brief narrative (50-100 words) about its creation, inspired by the visual details. Use markdown headers: # Title and # Narrative. Use {language} with a {tone} tone."
    return base_prompt 