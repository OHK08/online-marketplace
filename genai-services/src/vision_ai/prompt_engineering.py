# vision_ai/prompt_engineering.py

from textwrap import dedent

CRAFT_CONTEXT = {
    "general": {
        "keywords": ["handcrafted", "artisan", "heritage", "tradition", "sustainability"],
        "notes": "Emphasize cultural context, maker's intent, materials, and community value."
    },
    "pottery": {
        "keywords": ["wheel-throwing", "kiln", "glaze", "earthenware", "stoneware"],
        "notes": "Discuss clay preparation, shaping methods, firing traditions, and regional motifs."
    },
    "textiles": {
        "keywords": ["loom", "warp", "weft", "natural dyes", "embroidery", "block printing"],
        "notes": "Cover fiber sources, dyeing methods, weaving/printing techniques, and symbolism."
    },
    "woodwork": {
        "keywords": ["carving", "joinery", "lathe", "varnish", "grain"],
        "notes": "Highlight wood selection, carving styles, finishes, and regional design language."
    },
    "metalwork": {
        "keywords": ["forging", "casting", "annealing", "filigree", "patina"],
        "notes": "Include heating/cooling cycles, ornamental styles, and safety in handling metal."
    },
    "basketry": {
        "keywords": ["cane", "reed", "weave patterns", "coiling", "plaiting"],
        "notes": "Focus on plant materials, pattern logic, local ecology, and utility vs. ritual use."
    },
    "jewelry": {
        "keywords": ["gem setting", "bezel", "engraving", "alloy", "polish"],
        "notes": "Mention metal choice, stone symbolism, and craftsmanship traditions."
    },
    "painting": {
        "keywords": ["pigments", "gesso", "brushwork", "motifs", "iconography"],
        "notes": "Discuss surface prep, styles, and narrative/ritual meanings of motifs."
    }
}


def _craft_hints(craft_type: str) -> str:
    ct = (craft_type or "general").strip().lower()
    ctx = CRAFT_CONTEXT.get(ct, CRAFT_CONTEXT["general"])
    keywords = ", ".join(ctx["keywords"])
    notes = ctx["notes"]
    return f"- Craft type: {ct}\n- Useful keywords: {keywords}\n- Notes: {notes}"


def get_story_prompt(
    craft_type: str = "general",
    language: str = "English",
    tone: str = "warm, respectful, vivid",
    region_hint: str | None = None,
) -> str:
    """
    Returns a single, self-contained prompt string for a multimodal (image + text) request.
    Target model: Google Gemini (Vision). Output is markdown with strict section headers.
    """
    region_line = f"- Region/Culture hint: {region_hint}" if region_hint else "- Region/Culture hint: Use cues from the image."
    craft_hints = _craft_hints(craft_type)

    prompt = f"""
You are a cultural heritage storyteller and craft instructor.

Analyze the provided IMAGE of an artisan craft, identified as "{craft_type}". 
Use visual details (materials, tools, motifs, textures, patterns) to ground your writing.

Write in {language} with a {tone} tone.

Goals:
1) Produce a catchy Title.
2) Write an engaging Narrative about the craft's cultural significance (200–300 words), reflecting its {craft_type} heritage.
3) Provide a practical Tutorial (5–7 steps) tailored to {craft_type} techniques.

Constraints:
- Output FORMAT must be EXACTLY these markdown sections:
  # Title
  # Narrative (200–300 words)
  # Tutorial (5–7 steps)
- Do NOT include any preamble or explanations outside these sections.
- Keep the narrative between 200 and 300 words.
- The tutorial must have 5–7 numbered steps (1., 2., 3., ...).
- Prefer image evidence; if uncertain, use the hints below without inventing unverifiable specifics.
- Avoid repeating the same sentence openings; vary rhythm and phrasing.

Context Hints:
{craft_hints}
{region_line}

Safety & Style:
- Be culturally respectful and accurate; avoid stereotypes.
- No personal data or unsafe instructions.
- If the image contradicts the supplied craft_type, prioritize what’s visible in the image but keep {craft_type} as the guiding theme.

Now return ONLY the three sections in markdown with the required headers and counts.
""".strip()

    # Dedent for cleanliness (not required, but keeps logs neat)
    return dedent(prompt)
