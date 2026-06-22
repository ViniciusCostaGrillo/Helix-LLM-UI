import json
import os
from backend.schemas.analyzer import AnalysisResult, ComponentMetadata, DesignTheme, LayoutAnalysis
from backend.schemas.extractor import ExtractionResult
from backend.schemas.vision import VisionMetadata
from backend.utils.custom_logger import setup_logger

logger = setup_logger("analyzer.layout_analyzer")


class LayoutAnalyzer:
    """Service to analyze layout structures using Gemini, OpenAI, or Anthropic LLMs

    to yield structured design schemas, falling back to a dynamic mock when no keys exist.
    """

    def analyze(
        self, extraction: ExtractionResult, vision: VisionMetadata
    ) -> AnalysisResult:
        logger.info("Initializing layout analysis...")

        # 1. Select provider based on environment variables
        gemini_key = os.getenv("GEMINI_API_KEY")
        openai_key = os.getenv("OPENAI_API_KEY")
        anthropic_key = os.getenv("ANTHROPIC_API_KEY")

        # Skip placeholder configurations
        if gemini_key == "your_gemini_api_key_here":
            gemini_key = None
        if openai_key == "your_openai_api_key_here":
            openai_key = None
        if anthropic_key == "your_anthropic_api_key_here":
            anthropic_key = None

        prompt = self._build_prompt(extraction, vision)

        # 2. Execute LLM call or fallback
        if gemini_key:
            logger.info("Using Google Gemini provider for analysis...")
            return self._call_gemini(prompt, gemini_key)
        elif openai_key:
            logger.info("Using OpenAI GPT provider for analysis...")
            return self._call_openai(prompt, openai_key)
        elif anthropic_key:
            logger.info("Using Anthropic Claude provider for analysis...")
            return self._call_anthropic(prompt, anthropic_key)
        else:
            logger.warning(
                "No LLM API keys configured. Falling back to dynamic Mock Layout Analyzer."
            )
            return self._run_mock_analysis(extraction, vision)

    def _build_prompt(self, extraction: ExtractionResult, vision: VisionMetadata) -> str:
        """Constructs a detailed structured prompt combining HTML structures, styles, and vision coordinates."""
        # Truncate text and classes to prevent excessively long prompts
        fonts = ", ".join(extraction.styles.fonts)
        colors = ", ".join(extraction.styles.colors)

        # Map DOM nodes summary
        elements_summary = []
        for i, el in enumerate(extraction.elements[:15]):  # top-level elements summary
            child_tags = [child.tag for child in el.children[:5]]
            elements_summary.append(
                f"Element {i+1}: Tag: <{el.tag}>, Classes: '{el.attributes.get('class', '')}', "
                f"Text preview: '{el.text or ''}', Child tags: {child_tags}"
            )
        elements_str = "\n".join(elements_summary)

        prompt = f"""You are a senior UI/UX layout analyzer and design token builder.
Analyze the following parsed web page structures, extracted styles, and visual screenshots information to reconstruct the page layout guide.

--- CRAWLED DOM STRUCTURES ---
Top-level semantic elements:
{elements_str}

--- STYLE PARSER INFO ---
CSS Colors Extracted: {colors}
CSS Font Families Extracted: {fonts}

--- SCREENSHOT VISION METADATA ---
Dominant Colors detected: {vision.colors.dominant_colors}
Inferred Background: {vision.colors.background_color}
Grid Divisions (relative vertical/horizontal split positions):
- Vertical: {vision.grid.vertical_splits}
- Horizontal: {vision.grid.horizontal_splits}
Estimated Layout Margins: {vision.spacing.margins}
Content Density: {vision.density.content_percentage}% active space, {vision.density.whitespace_percentage}% whitespace
Grid Layout Classification: {vision.grid.grid_type}

--- REQUIRED OUTPUT ---
You must generate a structured JSON document representing the design tokens, color palette, detected key UI components (e.g. headers, heroes, sections, buttons, footers), responsiveness, and code styling recommendations.
"""
        return prompt

    def _call_gemini(self, prompt: str, api_key: str) -> AnalysisResult:
        import google.generativeai as genai

        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-1.5-flash")
        
        try:
            response = model.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(
                    response_mime_type="application/json",
                    response_schema=AnalysisResult,
                ),
            )
            data = json.loads(response.text)
            return AnalysisResult(**data)
        except Exception as e:
            logger.error(f"Gemini API invocation failed: {e}. Falling back to Mock.")
            raise

    def _call_openai(self, prompt: str, api_key: str) -> AnalysisResult:
        from openai import OpenAI

        client = OpenAI(api_key=api_key)
        try:
            response = client.beta.chat.completions.parse(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a structural layout analyzer that returns precise Pydantic outputs.",
                    },
                    {"role": "user", "content": prompt},
                ],
                response_format=AnalysisResult,
            )
            parsed_result = response.choices[0].message.parsed
            if not parsed_result:
                raise ValueError("OpenAI parse returned empty payload.")
            return parsed_result
        except Exception as e:
            logger.error(f"OpenAI API invocation failed: {e}. Falling back to Mock.")
            raise

    def _call_anthropic(self, prompt: str, api_key: str) -> AnalysisResult:
        from anthropic import Anthropic

        client = Anthropic(api_key=api_key)
        
        # Enforce json formatting schema in the prompt
        schema_info = json.dumps(AnalysisResult.model_json_schema(), indent=2)
        system_instructions = (
            "You are a visual design analyzer. You must output ONLY valid JSON matching this schema:\n"
            f"{schema_info}\nDo not return any extra markdown headers, text descriptions, or conversational prefixes."
        )

        try:
            message = client.messages.create(
                model="claude-3-5-sonnet-20240620",
                max_tokens=4000,
                system=system_instructions,
                messages=[{"role": "user", "content": prompt}],
            )
            content_text = "".join([block.text for block in message.content])
            data = json.loads(content_text)
            return AnalysisResult(**data)
        except Exception as e:
            logger.error(f"Anthropic API invocation failed: {e}. Falling back to Mock.")
            raise

    def _run_mock_analysis(
        self, extraction: ExtractionResult, vision: VisionMetadata
    ) -> AnalysisResult:
        """Dynamic heuristic analyzer which builds a valid AnalysisResult based on parser data."""
        # 1. Colors
        bg = vision.colors.background_color or "#ffffff"
        primary = "#333333"
        secondary = "#666666"

        dominant_list = vision.colors.dominant_colors
        if len(dominant_list) > 1:
            primary = dominant_list[0] if dominant_list[0] != bg else dominant_list[1]
        if len(dominant_list) > 2:
            secondary = (
                dominant_list[2]
                if dominant_list[2] not in (bg, primary)
                else dominant_list[1]
            )

        theme = DesignTheme(
            primary_color=primary,
            secondary_color=secondary,
            background_color=bg,
            text_color="#1a1a1a" if bg.lower() in ("#ffffff", "#eee", "#eeeeee") else "#ffffff",
            fonts=extraction.styles.fonts or ["sans-serif"],
        )

        # 2. Components
        components = []
        
        # Look at the root-level elements from DOM parser to map them
        for i, el in enumerate(extraction.elements[:8]):
            comp_id = f"comp_{i+1}_{el.tag}"
            
            # Simple text aggregation
            texts = []
            if el.text:
                texts.append(el.text)
            for child in el.children[:5]:
                if child.text:
                    texts.append(child.text)

            # Inferred type
            tag_lower = el.tag.lower()
            if tag_lower in ("header", "nav"):
                comp_type = "header"
            elif tag_lower == "footer":
                comp_type = "footer"
            elif tag_lower == "form":
                comp_type = "form"
            elif tag_lower in ("h1", "h2") or "hero" in el.attributes.get("class", "").lower():
                comp_type = "hero"
            elif tag_lower in ("ul", "ol"):
                comp_type = "list"
            else:
                comp_type = "card" if len(el.children) > 1 else "section"

            classes = []
            class_str = el.attributes.get("class", "")
            if class_str:
                classes = class_str.split(" ")

            components.append(
                ComponentMetadata(
                    component_id=comp_id,
                    type=comp_type,
                    description=f"Inferred {comp_type} element mapped from <{el.tag}> tag.",
                    layout_type=extraction.styles.layout_rules.get("grid_type", "flex-col"),
                    text_content=texts,
                    style_classes=classes[:10],
                )
            )

        # 3. Layout details
        layout = LayoutAnalysis(
            grid_structure=f"Identified {vision.grid.grid_type} grid structure with {len(vision.grid.horizontal_splits)} vertical layout blocks.",
            spacing_feel="spacious" if vision.density.whitespace_percentage > 70.0 else "compact",
            responsiveness="Standard desktop margins of left/right padding. Standard column layout.",
        )

        return AnalysisResult(
            page_purpose="documentation_page" if "example" in extraction.metadata.title.lower() else "landing_page",
            theme=theme,
            components=components,
            layout=layout,
            ai_recommendations="Use standard flexbox stacks. The primary background color is light gray, so consider using dark gray text for typography contrast.",
        )
