import os
import json
from backend.schemas.designer import VisualIntent, CreativeDirection
from backend.utils.custom_logger import setup_logger

logger = setup_logger("designer.creative_director_agent")


class CreativeDirectorAgent:
    """Agent that acts as a virtual Art Director to define typography, color palettes, and motion guidelines."""

    def define_direction(self, intent: VisualIntent, prompt: str) -> CreativeDirection:
        logger.info("CreativeDirectorAgent: defining artistic direction based on VisualIntent...")

        gemini_key = os.getenv("GEMINI_API_KEY")
        openai_key = os.getenv("OPENAI_API_KEY")
        anthropic_key = os.getenv("ANTHROPIC_API_KEY")

        # Clean placeholders
        if gemini_key == "your_gemini_api_key_here":
            gemini_key = None
        if openai_key == "your_openai_api_key_here":
            openai_key = None
        if anthropic_key == "your_anthropic_api_key_here":
            anthropic_key = None

        if gemini_key or openai_key or anthropic_key:
            try:
                return self._call_llm(intent, prompt, gemini_key, openai_key, anthropic_key)
            except Exception as e:
                logger.warning(f"LLM call failed in CreativeDirectorAgent: {e}. Falling back to rule-based direction.")

        return self._run_mock_direction(intent, prompt)

    def _call_llm(self, intent: VisualIntent, prompt: str, gemini_key, openai_key, anthropic_key) -> CreativeDirection:
        llm_prompt = f"""You are a Creative Director for Helix UI.
Review the original user prompt: "{prompt}" and the extracted VisualIntent: {intent.model_dump_json()}
Define the visual identity details, returning ONLY a valid JSON conforming to the CreativeDirection schema:
{{
  "direction_statement": "Artistic concept summary",
  "typography": ["list", "of", "Google Fonts family names"],
  "colors": ["List of hex colors matching the theme"],
  "animations": ["GSAP scroll triggers or animations presets"],
  "assets": ["required backgrounds, icons, videos assets"],
  "visual_hierarchy": ["guidelines detailing element dominance"]
}}
Return ONLY valid JSON. Do not include markdown code block formatting.
"""

        # Call OpenAI
        if openai_key:
            from openai import OpenAI
            base_url = os.getenv("OPENAI_API_BASE")
            model = os.getenv("OPENAI_MODEL_NAME", "gpt-4o-mini")
            client = OpenAI(api_key=openai_key, base_url=base_url)
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": llm_prompt}]
            )
            content = response.choices[0].message.content.strip()
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            return CreativeDirection.model_validate(json.loads(content))

        # Call Gemini
        elif gemini_key:
            import google.generativeai as genai
            genai.configure(api_key=gemini_key)
            model_name = os.getenv("GEMINI_MODEL_NAME", "gemini-1.5-pro")
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(llm_prompt)
            content = response.text.strip()
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            return CreativeDirection.model_validate(json.loads(content))

        # Call Anthropic
        elif anthropic_key:
            from anthropic import Anthropic
            client = Anthropic(api_key=anthropic_key)
            message = client.messages.create(
                model="claude-3-5-sonnet-20240620",
                max_tokens=1000,
                messages=[{"role": "user", "content": llm_prompt}]
            )
            content = "".join([block.text for block in message.content]).strip()
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            return CreativeDirection.model_validate(json.loads(content))

        raise RuntimeError("No LLM key configured")

    def _run_mock_direction(self, intent: VisualIntent, prompt: str) -> CreativeDirection:
        logger.info("CreativeDirectorAgent: executing local rule-based direction fallback.")
        style_list = [s.lower() for s in intent.style]

        # Primary style presets
        if "luxury" in style_list:
            statement = "High-end luxury aesthetic utilizing elegant typography contrast and sophisticated dark gold accents."
            typography = ["Playfair Display", "Inter"]
            colors = ["#0b0a0f", "#d4af37", "#f5f5f7", "#1a1824"]
            animations = ["Slow GSAP reveal", "Fade-in sections"]
            assets = ["premium_editorial_bg", "luxury_svg_icons"]
            hierarchy = ["Dominant product title", "Medium showcase cards", "Small editorial metadata"]
        elif "saas" in style_list or "technology" in intent.industry:
            statement = "Modern high-performance SaaS layout featuring clean grids, neon accent glows, and premium typography."
            typography = ["Inter", "Geist"]
            colors = ["#000000", "#0072f5", "#f4f4f5", "#8f8f93"]
            animations = ["GSAP hover cards scale", "Slide-up list items"]
            assets = ["grid_mesh_pattern", "tech_flat_icons"]
            hierarchy = ["Large bold header titles", "Structured metrics grid items", "Compact footers"]
        elif "minimal" in style_list:
            statement = "Clean minimalism focus emphasizing negative whitespace, crisp margins, and layout simplicity."
            typography = ["Helvetica Neue", "Inter"]
            colors = ["#fafafa", "#171717", "#e5e5e5", "#737373"]
            animations = ["Subtle fade reveals", "No scroll overrides"]
            assets = ["clean_whitespace_bg", "minimal_lines_icons"]
            hierarchy = ["Oversized font headers", "Single text column body", "Flat link layouts"]
        else:
            statement = "Dynamic editorial-focused interface balancing typographic presence and visual layout components."
            typography = ["Plus Jakarta Sans", "Inter"]
            colors = ["#0a0f1d", "#6366f1", "#f8fafc", "#475569"]
            animations = ["Subtle parallax transitions", "Smooth scroll anchors"]
            assets = ["colorful_gradients", "standard_vector_icons"]
            hierarchy = ["Hero title text", "Two-column description tables", "Centered link buttons"]

        return CreativeDirection(
            direction_statement=statement,
            typography=typography,
            colors=colors,
            animations=animations,
            assets=assets,
            visual_hierarchy=hierarchy
        )
