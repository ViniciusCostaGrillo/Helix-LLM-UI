import os
import sys
from pathlib import Path

# Ensure backend can be imported correctly
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from backend.dataset.builder import DatasetBuilder
from backend.schemas.analyzer import AnalysisResult
from backend.schemas.codegen import CodegenResult, GeneratedComponent
from backend.schemas.dataset_builder import DatasetManifest
from backend.schemas.extractor import ExtractionResult
from backend.schemas.vision import VisionMetadata
from backend.utils.custom_logger import setup_logger

logger = setup_logger("utils.test_dataset_builder")


def run_tests() -> None:
    logger.info("Initializing Dataset Builder Test Harness...")

    # Define paths
    base_dir = Path(__file__).resolve().parent.parent.parent
    playwright_dir = base_dir / "storage" / "test_crawl" / "playwright"

    html_path = playwright_dir / "page.html"
    screenshot_path = playwright_dir / "screenshot.png"
    extraction_path = playwright_dir / "extraction_result.json"
    vision_path = playwright_dir / "vision_metadata.json"
    analysis_path = playwright_dir / "metadata.json"
    components_dir = playwright_dir / "components"
    css_path = playwright_dir / "global_styles.css"

    # Verify input existence
    for path in [html_path, screenshot_path, extraction_path, vision_path, analysis_path, components_dir]:
        if not path.exists():
            logger.error(f"Input asset not found at: {path}")
            sys.exit(1)

    # 1. Load raw contents
    logger.info("Reading crawled source page.html...")
    with open(html_path, "r", encoding="utf-8") as f:
        raw_html = f.read()

    # 2. Parse JSON Pydantic data
    logger.info("Loading extractions and designs Pydantic JSON files...")
    try:
        with open(extraction_path, "r", encoding="utf-8") as f:
            extraction = ExtractionResult.model_validate_json(f.read())
        with open(vision_path, "r", encoding="utf-8") as f:
            vision = VisionMetadata.model_validate_json(f.read())
        with open(analysis_path, "r", encoding="utf-8") as f:
            analysis = AnalysisResult.model_validate_json(f.read())
        logger.info("[PASS] Input Pydantic models loaded successfully.")
    except Exception as e:
        logger.error(f"Failed to load input JSON models: {e}")
        sys.exit(1)

    # 3. Load React components code
    logger.info("Reading generated React component TSX files...")
    components = []
    for file in os.listdir(components_dir):
        if file.endswith(".tsx"):
            comp_name = file.replace(".tsx", "")
            comp_path = components_dir / file
            with open(comp_path, "r", encoding="utf-8") as f:
                code = f.read()
            components.append(
                GeneratedComponent(
                    name=comp_name,
                    code=code,
                    description=f"React component {comp_name} loaded from storage."
                )
            )

    global_styles = None
    if css_path.exists():
        with open(css_path, "r", encoding="utf-8") as f:
            global_styles = f.read()

    codegen = CodegenResult(
        components=components,
        global_styles=global_styles
    )

    # 4. Trigger Builder
    # Specify custom test dataset directory: base_dir / "dataset"
    builder = DatasetBuilder(base_dataset_path=str(base_dir / "dataset"))
    try:
        site_dir = builder.build_package(
            site_id=1,
            url="https://example.com",
            raw_html=raw_html,
            screenshot_path=str(screenshot_path),
            extraction=extraction,
            vision=vision,
            analysis=analysis,
            codegen=codegen
        )
    except Exception as e:
        logger.exception(f"DatasetBuilder packaging failed: {e}")
        sys.exit(1)

    # 5. Assertions on generated package
    logger.info("Verifying generated package structures...")
    site_path = Path(site_dir)
    manifest_path = site_path / "manifest.json"

    assert site_path.exists(), "Dataset site folder not created!"
    assert (site_path / "raw_html.html").exists(), "raw_html.html missing from package!"
    assert (site_path / "screenshot.png").exists(), "screenshot.png missing from package!"
    assert (site_path / "extraction_result.json").exists(), "extraction_result.json missing from package!"
    assert (site_path / "vision_metadata.json").exists(), "vision_metadata.json missing from package!"
    assert (site_path / "layout_analysis.json").exists(), "layout_analysis.json missing from package!"
    assert manifest_path.exists(), "manifest.json index missing from package!"

    # Verify React component files are copied inside components subfolder
    for comp in components:
        comp_file = site_path / "components" / f"{comp.name}.tsx"
        assert comp_file.exists(), f"React component file {comp_file.name} missing from packaged components directory!"

    # Verify manifest JSON details
    try:
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = DatasetManifest.model_validate_json(f.read())
        logger.info(f"Loaded generated manifest: {manifest.site_id}")
        
        assert manifest.site_id == "site_000001", "Manifest site_id mismatch!"
        assert manifest.url == "https://example.com", "Manifest url mismatch!"
        assert manifest.components_count == len(components), "Manifest components_count mismatch!"
        assert manifest.primary_color == analysis.theme.primary_color, "Manifest primary color mismatch!"
        assert manifest.background_color == analysis.theme.background_color, "Manifest background color mismatch!"
        assert manifest.content_density == vision.density.content_percentage, "Manifest content density mismatch!"
        
        logger.info("[PASS] Dataset manifest assertions passed.")
    except Exception as e:
        logger.error(f"Manifest validations failed: {e}")
        sys.exit(1)

    logger.info("ALL DATASET BUILDER CHECKS PASSED SUCCESSFULLY!")


if __name__ == "__main__":
    run_tests()
