# genai-services/src/vision_ai/prompts/prompt_engineering.py
def get_story_prompt(craft_type: str, language: str, tone: str) -> str:
    # Craft-specific guidance
    craft_guidelines = {
        "pottery": "Focus on wheel-throwing or hand-building, clay types, and firing.",
        "basket": "Highlight weaving patterns, natural fibers, and craftsmanship.",
        "weaving": "Emphasize loom techniques, thread types, and patterns."
    }
    guideline = craft_guidelines.get(craft_type, "Describe the craft's techniques and materials.")
    
    # Style consistency
    style_template = f"Use a {tone} tone with vivid, respectful language about artisans."
    
    base_prompt = f"Write a story about this {craft_type} craft image. {guideline} {style_template} Include these sections with headers: # Title (5-10 words), # Narrative (at least 100 words) on its creation, # Tutorial (at least 50 words) with 3-4 steps, # Categories (3-4 relevant ones). Ensure all sections are present and clear. Use {language}."
    return base_prompt