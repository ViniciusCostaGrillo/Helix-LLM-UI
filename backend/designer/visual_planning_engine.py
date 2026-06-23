from backend.schemas.designer import VisualPlan
from backend.designer.designer_agent import DesignerAgent
from backend.designer.creative_director_agent import CreativeDirectorAgent
from backend.designer.moodboard_engine import MoodboardEngine
from backend.designer.style_composer import StyleComposer
from backend.designer.reference_composer import ReferenceComposer
from backend.utils.custom_logger import setup_logger

logger = setup_logger("designer.visual_planning_engine")


class VisualPlanningEngine:
    """Orchestrator engine that compiles a visual plan detailing styles, layout order, and themes prior to codegen."""

    def __init__(self) -> None:
        self.designer = DesignerAgent()
        self.creative_director = CreativeDirectorAgent()
        self.moodboard_engine = MoodboardEngine()
        self.style_composer = StyleComposer()
        self.reference_composer = ReferenceComposer()

    def plan(self, prompt: str) -> VisualPlan:
        logger.info(f"VisualPlanningEngine: constructing visual plan for prompt: '{prompt}'...")

        # 1. Analyze prompt to construct visual intent
        intent = self.designer.analyze(prompt)

        # 2. Refine design variables via Creative Director
        direction = self.creative_director.define_direction(intent, prompt)

        # 3. Resolve or load moodboard preset matching the primary style target
        primary_style = intent.style[0] if intent.style else "minimal"
        moodboard = self.moodboard_engine.load_or_create(primary_style)

        # 4. Compose unified composite style tag title
        composite_theme = self.style_composer.compose_style_tag(intent.style)

        # 5. Query and compose references list from collections
        references = self.reference_composer.compose_references(prompt)

        # 6. Design component order / layout schema matching category context
        layout = ["header", "hero", "features", "cta", "footer"]
        category_lower = intent.category.lower()
        if "ecommerce" in category_lower or "store" in category_lower:
            layout = ["header", "hero", "products_showcase", "details_split", "newsletter", "footer"]
        elif "dashboard" in category_lower or "console" in category_lower:
            layout = ["sidebar", "navbar", "metrics_grid", "analytics_chart", "activity_table"]
        elif "portfolio" in category_lower or "gallery" in category_lower:
            layout = ["header", "profile_hero", "gallery_grid", "contact_form", "footer"]

        # 7. Establish visual planning variables matching intent settings
        spacing = "modern"
        if "luxury" in intent.style or "editorial" in intent.style:
            spacing = "spacious"
        elif "dashboard" in category_lower:
            spacing = "compact"

        animations = "simple"
        if "active" in intent.animations:
            animations = "gsap"

        scroll = "normal"
        if "active" in intent.animations or "luxury" in intent.style or "editorial" in intent.style:
            scroll = "lenis"

        background = "solid"
        p_lower = prompt.lower()
        if "gradient" in p_lower or "luxury" in intent.style:
            background = "premium_gradient"
        elif "grid" in p_lower or "mesh" in p_lower or "saas" in intent.style:
            background = "mesh_grid"

        plan = VisualPlan(
            layout=layout,
            theme=composite_theme,
            spacing=spacing,
            animations=animations,
            scroll=scroll,
            background=background,
            references=references,
            visual_intent=intent,
            creative_direction=direction,
            moodboard=moodboard
        )

        logger.info(f"VisualPlanningEngine: successfully compiled VisualPlan with theme '{composite_theme}'.")
        return plan
