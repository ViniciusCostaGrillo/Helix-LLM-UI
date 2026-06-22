import os
import shutil
from datetime import datetime, timezone
from backend.schemas.analyzer import AnalysisResult
from backend.schemas.codegen import CodegenResult
from backend.schemas.dataset_builder import DatasetManifest
from backend.schemas.extractor import ExtractionResult
from backend.schemas.vision import VisionMetadata
from backend.utils.custom_logger import setup_logger

logger = setup_logger("dataset.builder")


class DatasetBuilder:
    """Service to package raw crawled source code, visual configurations, layout guides,

    and generated React components into standard structured datasets (e.g. site_000001/).
    """

    def __init__(self, base_dataset_path: str = "dataset") -> None:
        self.base_path = os.path.abspath(base_dataset_path)
        logger.debug(f"DatasetBuilder initialized with root path: {self.base_path}")

    def build_package(
        self,
        site_id: int,
        url: str,
        raw_html: str,
        screenshot_path: str,
        extraction: ExtractionResult,
        vision: VisionMetadata,
        analysis: AnalysisResult,
        codegen: CodegenResult,
    ) -> str:
        # 1. Format site name
        site_name = f"site_{site_id:06d}"
        site_dir = os.path.join(self.base_path, site_name)
        components_dir = os.path.join(site_dir, "components")

        logger.info(f"Building dataset package: {site_name} inside {site_dir}...")

        # 2. Create directories
        os.makedirs(site_dir, exist_ok=True)
        os.makedirs(components_dir, exist_ok=True)

        files_mapping = {}

        # 3. Save raw_html.html
        html_file = "raw_html.html"
        html_path = os.path.join(site_dir, html_file)
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(raw_html)
        files_mapping[html_file] = f"Relative path to {html_file}"
        logger.debug("Saved raw HTML source.")

        # 4. Copy screenshot.png
        screenshot_file = "screenshot.png"
        screenshot_dest = os.path.join(site_dir, screenshot_file)
        if os.path.exists(screenshot_path):
            shutil.copy(screenshot_path, screenshot_dest)
            files_mapping[screenshot_file] = f"Relative path to {screenshot_file}"
            logger.debug("Copied screenshot binary file.")
        else:
            logger.warning(f"Source screenshot not found at: {screenshot_path}")

        # 5. Save extraction_result.json
        ext_file = "extraction_result.json"
        ext_path = os.path.join(site_dir, ext_file)
        with open(ext_path, "w", encoding="utf-8") as f:
            f.write(extraction.model_dump_json(indent=2))
        files_mapping[ext_file] = f"Relative path to {ext_file}"

        # 6. Save vision_metadata.json
        vis_file = "vision_metadata.json"
        vis_path = os.path.join(site_dir, vis_file)
        with open(vis_path, "w", encoding="utf-8") as f:
            f.write(vision.model_dump_json(indent=2))
        files_mapping[vis_file] = f"Relative path to {vis_file}"

        # 7. Save layout_analysis.json
        lay_file = "layout_analysis.json"
        lay_path = os.path.join(site_dir, lay_file)
        with open(lay_path, "w", encoding="utf-8") as f:
            f.write(analysis.model_dump_json(indent=2))
        files_mapping[lay_file] = f"Relative path to {lay_file}"

        # 8. Save components
        for comp in codegen.components:
            comp_file = f"components/{comp.name}.tsx"
            comp_path = os.path.join(site_dir, comp_file)
            with open(comp_path, "w", encoding="utf-8") as f:
                f.write(comp.code)
            files_mapping[comp_file] = f"Relative path to {comp_file}"
        logger.debug(f"Saved {len(codegen.components)} React component files.")

        # 9. Save global_styles.css
        if codegen.global_styles:
            css_file = "global_styles.css"
            css_path = os.path.join(site_dir, css_file)
            with open(css_path, "w", encoding="utf-8") as f:
                f.write(codegen.global_styles)
            files_mapping[css_file] = f"Relative path to {css_file}"

        # 10. Generate manifest.json
        manifest = DatasetManifest(
            site_id=site_name,
            url=url,
            created_at=datetime.now(timezone.utc).isoformat(),
            components_count=len(codegen.components),
            primary_color=analysis.theme.primary_color,
            background_color=analysis.theme.background_color,
            content_density=vision.density.content_percentage,
            files_mapping=files_mapping,
        )

        manifest_file = "manifest.json"
        manifest_path = os.path.join(site_dir, manifest_file)
        with open(manifest_path, "w", encoding="utf-8") as f:
            f.write(manifest.model_dump_json(indent=2))

        logger.info(f"Successfully packaged {site_name} layout dataset.")
        return site_dir
