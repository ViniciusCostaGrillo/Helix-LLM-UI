import os
import json
from backend.schemas.designer import VisualIntent
from backend.utils.custom_logger import setup_logger

logger = setup_logger("designer.designer_agent")


class DesignerAgent:
    """Agent that interprets user prompt requirements into a structured VisualIntent."""

    def analyze(self, prompt: str) -> VisualIntent:
        logger.info(f"DesignerAgent: analyzing user prompt: '{prompt}'...")

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
                return self._call_llm(prompt, gemini_key, openai_key, anthropic_key)
            except Exception as e:
                logger.warning(f"LLM call failed in DesignerAgent: {e}. Falling back to rule-based parser.")

        return self._run_mock_analysis(prompt)

    def _call_llm(self, prompt: str, gemini_key, openai_key, anthropic_key) -> VisualIntent:
        llm_prompt = f"""You are a senior UI/UX Designer Agent.
Analyze the user prompt: "{prompt}"
Translate it into a structured JSON conforming exactly to the VisualIntent schema:
{{
  "industry": "e.g. fashion, technology, healthcare",
  "category": "e.g. ecommerce, landing page, dashboard, portfolio",
  "style": ["list", "of", "styles", "e.g.", "luxury", "minimal", "saas", "editorial", "glassmorphism"],
  "theme": ["dark", "and/or", "light"],
  "animations": ["subtle", "active", "or", "none"],
  "priority": ["list", "of", "elements", "to", "prioritize"]
}}
Return ONLY valid JSON. Do not include markdown code block formatting.
"""

        # Call OpenAI if present (highest priority for structured outputs)
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
            # Clean markdown code block if present
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            return VisualIntent.model_validate(json.loads(content))

        # Call Gemini
        elif gemini_key:
            import google.generativeai as genai
            genai.configure(api_key=gemini_key)
            model = genai.GenerativeModel("gemini-1.5-flash")
            response = model.generate_content(llm_prompt)
            content = response.text.strip()
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            return VisualIntent.model_validate(json.loads(content))

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
            return VisualIntent.model_validate(json.loads(content))

        raise RuntimeError("No LLM key configured")

    def _run_mock_analysis(self, prompt: str) -> VisualIntent:
        logger.info("DesignerAgent: executing local rule-based heuristic fallback parser.")
        p_lower = prompt.lower()

        # Heuristics
        industry = "general"
        category = "landing page"
        styles = ["minimal"]
        theme = ["dark"]
        animations = ["subtle"]
        priorities = ["layout", "typography"]

        # Industry
        if "footwear" in p_lower or "shoes" in p_lower or "clothing" in p_lower or "fashion" in p_lower:
            industry = "fashion"
            styles = ["luxury", "editorial"]
        elif "saas" in p_lower or "software" in p_lower or "tech" in p_lower:
            industry = "technology"
            styles = ["saas", "minimal"]
        elif "finance" in p_lower or "bank" in p_lower:
            industry = "finance"
            styles = ["saas", "dashboard"]

        # Category
        if "ecommerce" in p_lower or "store" in p_lower or "shop" in p_lower:
            category = "ecommerce"
            priorities = ["product showcase", "checkout ease"]
        elif "dashboard" in p_lower or "console" in p_lower or "metrics" in p_lower:
            category = "dashboard"
            priorities = ["data density", "grid layouts"]
        elif "portfolio" in p_lower or "gallery" in p_lower:
            category = "portfolio"
            priorities = ["media display", "typography"]

        # Style overlays
        if "luxury" in p_lower:
            if "luxury" not in styles:
                styles.append("luxury")
        if "editorial" in p_lower:
            if "editorial" not in styles:
                styles.append("editorial")
        if "glassmorphism" in p_lower or "glass" in p_lower:
            styles.append("glassmorphism")
        if "minimal" in p_lower:
            if "minimal" not in styles:
                styles.append("minimal")

        # Theme
        if "light" in p_lower:
            theme = ["light"]
        elif "dark" in p_lower:
            theme = ["dark"]

        # Animations
        if "active" in p_lower or "rich" in p_lower or "animation" in p_lower:
            animations = ["active"]
        elif "none" in p_lower or "static" in p_lower:
            animations = ["none"]

        return VisualIntent(
            industry=industry,
            category=category,
            style=styles,
            theme=theme,
            animations=animations,
            priority=priorities
        )
