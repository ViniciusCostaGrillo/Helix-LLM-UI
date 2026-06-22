import sys
from pathlib import Path

# Ensure backend can be imported correctly
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from backend.analyzer.layout_analyzer import LayoutAnalyzer
from backend.schemas.extractor import ExtractionResult
from backend.schemas.vision import VisionMetadata
from backend.utils.custom_logger import setup_logger

logger = setup_logger("utils.test_analyzer")


def run_tests() -> None:
    logger.info("Initializing Layout Analyzer Test Harness...")

    # Define paths
    base_dir = Path(__file__).resolve().parent.parent.parent
    playwright_dir = base_dir / "storage" / "test_crawl" / "playwright"

    extraction_path = playwright_dir / "extraction_result.json"
    vision_path = playwright_dir / "vision_metadata.json"

    if not extraction_path.exists():
        logger.error(f"Extraction file not found at: {extraction_path}")
        sys.exit(1)

    if not vision_path.exists():
        logger.error(f"Vision metadata file not found at: {vision_path}")
        sys.exit(1)

    # 1. Load data
    logger.info("Loading extraction result and vision metadata JSON files...")
    with open(extraction_path, "r", encoding="utf-8") as f:
        extraction_data = f.read()

    with open(vision_path, "r", encoding="utf-8") as f:
        vision_data = f.read()

    # Validate back to Pydantic objects
    try:
        extraction = ExtractionResult.model_validate_json(extraction_data)
        vision = VisionMetadata.model_validate_json(vision_data)
        logger.info("Successfully validated files back into Pydantic models.")
    except Exception as e:
        logger.error(f"Failed to validate input files against Pydantic models: {e}")
        sys.exit(1)

    # 2. Run Analyzer
    analyzer = LayoutAnalyzer()
    try:
        result = analyzer.analyze(extraction, vision)
    except Exception as e:
        logger.exception(f"Analyzer service failed with exception: {e}")
        sys.exit(1)

    # 3. Output results
    logger.info("------------- Verification Results -------------")
    logger.info(f"Page Purpose: {result.page_purpose}")
    logger.info(f"Theme Colors: Primary={result.theme.primary_color}, Secondary={result.theme.secondary_color}, Bg={result.theme.background_color}")
    logger.info(f"Fonts Mapped: {result.theme.fonts}")
    logger.info(f"Component count detected: {len(result.components)}")
    logger.info(f"Layout summary: {result.layout.grid_structure}")
    logger.info(f"AI Recommendations: {result.ai_recommendations}")

    # Assertions
    logger.info("Running validation checks...")

    assert result.page_purpose is not None, "Page purpose is null!"
    assert result.theme.primary_color.startswith("#"), "Primary color must be hex!"
    assert result.theme.secondary_color.startswith("#"), "Secondary color must be hex!"
    assert result.theme.background_color.startswith("#"), "Background color must be hex!"
    assert len(result.components) > 0, "No UI components detected!"

    for comp in result.components:
        assert comp.component_id is not None, "Component ID missing!"
        assert comp.type is not None, "Component type missing!"
        assert comp.description is not None, "Component description missing!"

    logger.info("[PASS] Analyzer schemas validation checks passed.")

    # 4. Export JSON
    try:
        json_data = result.model_dump_json(indent=2)
        logger.info("Pydantic Schema Serialization check passed.")

        # Write output metadata JSON
        output_json_path = playwright_dir / "metadata.json"
        with open(output_json_path, "w", encoding="utf-8") as out_f:
            out_f.write(json_data)
        logger.info(f"Metadata serialized and saved to: {output_json_path}")
    except Exception as e:
        logger.error(f"Failed metadata schema serialization check: {e}")
        sys.exit(1)

    logger.info("ALL ANALYZER CHECKS PASSED SUCCESSFULLY!")


if __name__ == "__main__":
    run_tests()
