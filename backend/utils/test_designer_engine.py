import os
import sys
from fastapi.testclient import TestClient

from backend.api.main import app
from backend.designer.designer_agent import DesignerAgent
from backend.designer.creative_director_agent import CreativeDirectorAgent
from backend.designer.moodboard_engine import MoodboardEngine
from backend.designer.style_composer import StyleComposer
from backend.designer.reference_composer import ReferenceComposer
from backend.designer.visual_planning_engine import VisualPlanningEngine
from backend.schemas.designer import VisualIntent, CreativeDirection, Moodboard, VisualPlan

client = TestClient(app)


def run_tests():
    print("Running Designer Engine validation suite...")
    success = True

    # 1. Designer Agent
    try:
        agent = DesignerAgent()
        intent = agent.analyze("Create a luxury footwear boutique store")
        assert isinstance(intent, VisualIntent)
        assert intent.industry == "fashion"
        assert intent.category == "ecommerce"
        assert "luxury" in intent.style
        print("PASS - DesignerAgent analysis")
    except Exception as e:
        print(f"FAIL - DesignerAgent analysis: {e}")
        success = False

    # 2. Creative Director Agent
    try:
        intent = VisualIntent(
            industry="fashion",
            category="ecommerce",
            style=["luxury", "editorial"],
            theme=["dark"],
            animations=["active"],
            priority=["typography"]
        )
        agent = CreativeDirectorAgent()
        direction = agent.define_direction(intent, "Create a luxury footwear boutique store")
        assert isinstance(direction, CreativeDirection)
        assert len(direction.typography) > 0
        assert len(direction.colors) > 0
        assert any(t in direction.typography for t in ["Playfair Display", "Inter"])
        print("PASS - CreativeDirectorAgent direction definition")
    except Exception as e:
        print(f"FAIL - CreativeDirectorAgent direction definition: {e}")
        success = False

    # 3. Moodboard Engine
    try:
        engine = MoodboardEngine()
        moodboard = engine.load_or_create("luxury")
        assert isinstance(moodboard, Moodboard)
        assert moodboard.style == "luxury"
        assert len(moodboard.colors) > 0
        assert "Playfair Display" in moodboard.typography

        # Test nonexistent dynamic moodboard
        custom_style = "dynamic_glass"
        mb = engine.load_or_create(custom_style)
        assert mb.style == "dynamic_glass"
        assert len(mb.colors) > 0
        
        file_path = engine.moodboards_dir / "dynamic_glass.json"
        assert file_path.exists()
        if file_path.exists():
            os.remove(file_path)
        print("PASS - MoodboardEngine load/create")
    except Exception as e:
        print(f"FAIL - MoodboardEngine load/create: {e}")
        success = False

    # 4. Style Composer
    try:
        composer = StyleComposer()
        tag = composer.compose_style_tag(["Luxury", "Glassmorphism ", "luxury", "Editorial"])
        assert tag == "luxury-glassmorphism-editorial"

        props = composer.resolve_style_properties(["luxury", "editorial"])
        assert any(f in props["fonts"] for f in ["Lora", "Playfair Display"])
        assert "#d4af37" in props["colors"]
        print("PASS - StyleComposer compose style tags and properties")
    except Exception as e:
        print(f"FAIL - StyleComposer compose style tags and properties: {e}")
        success = False

    # 5. Reference Composer
    try:
        composer = ReferenceComposer()
        refs = composer.compose_references("Create a premium landing page")
        assert isinstance(refs, list)
        assert len(refs) > 0
        assert any(r in refs for r in ["elara", "noirframe", "refokus", "linear", "stripe"])
        print("PASS - ReferenceComposer compose design references")
    except Exception as e:
        print(f"FAIL - ReferenceComposer compose design references: {e}")
        success = False

    # 6. Visual Planning Engine
    try:
        engine = VisualPlanningEngine()
        plan = engine.plan("Create a luxury footwear ecommerce website")
        assert isinstance(plan, VisualPlan)
        assert plan.theme == "luxury-editorial"
        assert plan.spacing == "spacious"
        assert "hero" in plan.layout
        assert "products_showcase" in plan.layout
        print("PASS - VisualPlanningEngine plan compile")
    except Exception as e:
        print(f"FAIL - VisualPlanningEngine plan compile: {e}")
        success = False

    # 7. FastAPI Endpoint
    try:
        response = client.post(
            "/generation/visual_plan",
            json={"prompt": "Create a luxury footwear ecommerce website"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "layout" in data
        assert "theme" in data
        assert "visual_intent" in data
        assert "creative_direction" in data
        assert "moodboard" in data
        assert data["theme"] == "luxury-editorial"
        print("PASS - FastAPI POST /generation/visual_plan")
    except Exception as e:
        print(f"FAIL - FastAPI POST /generation/visual_plan: {e}")
        success = False

    if not success:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    run_tests()
