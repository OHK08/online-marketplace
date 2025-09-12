# genai-services/src/vision_ai/prompts/prompt_engineering.py
def get_story_prompt(craft_type: str, language: str, tone: str) -> str:
    # Craft-specific guidance
    craft_guidelines = {
        "pottery": "Emphasize wheel-throwing or hand-building techniques, clay types, and firing processes.",
        "basket": "Focus on weaving patterns, natural fibers, and traditional craftsmanship.",
        "weaving": "Highlight loom techniques, thread types, and cultural patterns."
    }
    guideline = craft_guidelines.get(craft_type, "Describe the craft's unique techniques and materials in detail.")
    
    # Style consistency template
    style_template = f"Maintain a consistent {tone} tone throughout, using vivid descriptions and respectful language toward artisans to ensure a professional and engaging narrative."
    
    # Explicit section requirements with examples
    section_example = """
    Example format:
    {
        "title": "Handmade Clay Pot of Timeless Craft",
        "narrative": "Originating from ancient villages, this pot is crafted using local clay... (100-200 words)",
        "tutorial": "1. Prepare clay. 2. Shape on wheel. 3. Fire in kiln... (50-100 words, 3-5 steps)",
        "categories": ["pottery", "handmade", "traditional"] (3-5 categories)
    }
    """
    
    base_prompt = f"Create a detailed story about this {craft_type} craft image. {guideline} {style_template} {section_example} Return ONLY a JSON object with these keys: 'title' (5-10 words), 'narrative' (100-200 words about its creation), 'tutorial' (50-100 words with 3-5 clear steps), 'categories' (list of 3-5 relevant categories). Use {language} and include all keys or regenerate."
    return base_prompt