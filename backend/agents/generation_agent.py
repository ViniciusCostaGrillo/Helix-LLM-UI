import logging
import os
from pathlib import Path

from PIL import Image

from backend.analyzer.layout_analyzer import LayoutAnalyzer
from backend.codegen.code_generator import CodeGenerator
from backend.dataset.builder import DatasetBuilder
from backend.schemas.dataset_builder import DatasetManifest
from backend.schemas.extractor import ExtractedStyles, ExtractionResult, PageMetadata, SemanticElement
from backend.schemas.rag import RAGQueryRequest
from backend.schemas.vision import ColorPalette, GridLayout, SpacingMetrics, VisualDensity, VisionMetadata
from backend.rag.service import RAGService
from backend.designer.visual_planning_engine import VisualPlanningEngine

logger = logging.getLogger(__name__)


class GenerationAgent:
    """Agent implementing the end-to-end prompt-to-code generation flow.

    Retrieves context using RAG, resolves design guidelines, generates React/Tailwind
    code, saves files, and loops back to index outputs back to the vector DB.
    """

    def __init__(self) -> None:
        self.rag = RAGService()
        self.analyzer = LayoutAnalyzer()
        self.generator = CodeGenerator()

    def run(self, prompt: str, project_id: str, execution_id: str) -> dict:
        logger.info(f"GenerationAgent: starting prompt-to-code pipeline for project {project_id}...")

        # 1. Query RAG context matching prompt
        logger.info("GenerationAgent: fetching RAG context from ChromaDB...")
        try:
            self.rag.query(RAGQueryRequest(prompt=prompt, limit=3))
        except Exception as e:
            logger.warning(f"RAG query failed: {e}. Running with empty context.")


        # 2. Call the Visual Planning Engine to build a structured Visual Plan
        logger.info("GenerationAgent: running Visual Planning Engine...")
        visual_planner = VisualPlanningEngine()
        visual_plan = visual_planner.plan(prompt)

        # Extract design hints from Visual Plan
        colors_list = visual_plan.creative_direction.colors
        bg_color = colors_list[0] if len(colors_list) > 0 else "#ffffff"
        primary_color = colors_list[1] if len(colors_list) > 1 else "#3b82f6"
        secondary_color = colors_list[2] if len(colors_list) > 2 else "#10b981"
        text_color = colors_list[3] if len(colors_list) > 3 else "#1f2937"
        
        fonts = visual_plan.creative_direction.typography if visual_plan.creative_direction.typography else ["Inter"]

        # 3. Create synthetic ExtractionResult and VisionMetadata representing the plan layout
        elements = []
        for name in visual_plan.layout:
            tag = "section"
            if name == "header":
                tag = "header"
            elif name == "footer":
                tag = "footer"
            elif name in ["sidebar", "aside"]:
                tag = "aside"
            elif name == "navbar":
                tag = "nav"
            elements.append(SemanticElement(
                tag=tag,
                text=f"{name.capitalize()} component layout placeholder based on design guidelines.",
                children=[]
            ))

        extraction = ExtractionResult(
            metadata=PageMetadata(title=f"Generated {project_id}", description=prompt),
            styles=ExtractedStyles(colors=[bg_color, primary_color, secondary_color, text_color], fonts=fonts),
            elements=elements,
            clean_text=prompt
        )

        margins_val = {"top": 20, "bottom": 20, "left": 40, "right": 40}
        if visual_plan.spacing == "spacious":
            margins_val = {"top": 40, "bottom": 40, "left": 80, "right": 80}
        elif visual_plan.spacing == "compact":
            margins_val = {"top": 10, "bottom": 10, "left": 20, "right": 20}

        vision = VisionMetadata(
            colors=ColorPalette(background_color=bg_color, dominant_colors=[bg_color, primary_color, secondary_color]),
            grid=GridLayout(grid_type="dashboard" if visual_plan.visual_intent.category == "dashboard" else "grid", vertical_splits=[], horizontal_splits=[]),
            spacing=SpacingMetrics(margins=margins_val),
            density=VisualDensity(content_percentage=50, whitespace_percentage=50),
        )

        # 4. Generate Layout Design Guidelines
        analysis_res = self.analyzer.analyze(extraction, vision)

        # Force analysis theme mapping
        analysis_res.theme.primary_color = primary_color
        analysis_res.theme.secondary_color = secondary_color
        analysis_res.theme.background_color = bg_color
        analysis_res.theme.text_color = text_color

        # 5. Generate Code Components
        codegen_res = self.generator.generate(extraction, analysis_res)

        # 6. Save component TSX modules to project output directory
        base_dir = Path(__file__).resolve().parent.parent.parent
        project_dir = base_dir / "storage" / "projects" / str(project_id)
        components_dir = project_dir / "components"
        os.makedirs(components_dir, exist_ok=True)

        for comp in codegen_res.components:
            comp_file = components_dir / f"{comp.name}.tsx"
            with open(comp_file, "w", encoding="utf-8") as f:
                f.write(comp.code)

        if codegen_res.global_styles:
            styles_file = project_dir / "global_styles.css"
            with open(styles_file, "w", encoding="utf-8") as f:
                f.write(codegen_res.global_styles)

        # 7. Save a mock screenshot for packaging
        screenshot_path = project_dir / "screenshot.png"
        img = Image.new("RGB", (800, 600), color=bg_color)
        img.save(screenshot_path)

        # 8. Package output as dataset item using DatasetBuilder
        builder = DatasetBuilder(base_dataset_path=str(base_dir / "dataset"))
        raw_html = f"<!DOCTYPE html><html><head><title>{extraction.metadata.title}</title></head><body>"
        for el in elements:
            raw_html += f"<{el.tag}>{el.text}</{el.tag}>"
        raw_html += "</body></html>"

        site_id = int(project_id) if project_id.isdigit() else 999
        site_dir = builder.build_package(
            site_id=site_id,
            url=f"https://generated-ui-{project_id}.local",
            raw_html=raw_html,
            screenshot_path=screenshot_path,
            extraction=extraction,
            vision=vision,
            analysis=analysis_res,
            codegen=codegen_res,
        )

        # 9. Embed and index/upsert back into ChromaDB to grow dataset continuously!
        logger.info("GenerationAgent: indexing generated components back into ChromaDB...")
        with open(Path(site_dir) / "manifest.json", "r", encoding="utf-8") as f:
            manifest = DatasetManifest.model_validate_json(f.read())

        # Page indexing
        page_text = f"Layout: {manifest.site_id} generated from prompt '{prompt}'. Colors: {manifest.primary_color}, {manifest.background_color}."
        page_vector = self.rag.generator.get_embedding(page_text)
        self.rag.chroma.upsert(
            collection_name="pages",
            doc_id=manifest.site_id,
            vector=page_vector,
            document=page_text,
            metadata={"url": manifest.url, "site_id": manifest.site_id, "prompt": prompt},
        )

        # Style indexing
        style_text = f"Style palette for prompt '{prompt}'. Colors: {manifest.primary_color}, {manifest.background_color}"
        style_vector = self.rag.generator.get_embedding(style_text)
        self.rag.chroma.upsert(
            collection_name="styles",
            doc_id=manifest.site_id,
            vector=style_vector,
            document=style_text,
            metadata={"site_id": manifest.site_id},
        )

        # Components indexing
        components_indexed = 0
        comp_dir = Path(site_dir) / "components"
        if comp_dir.exists():
            for file in os.listdir(comp_dir):
                if file.endswith(".tsx"):
                    comp_name = file.replace(".tsx", "")
                    with open(comp_dir / file, "r", encoding="utf-8") as cf:
                        comp_code = cf.read()
                    comp_vector = self.rag.generator.get_embedding(comp_code)
                    doc_id = f"{manifest.site_id}_{comp_name}"
                    self.rag.chroma.upsert(
                        collection_name="components",
                        doc_id=doc_id,
                        vector=comp_vector,
                        document=comp_code,
                        metadata={"site_id": manifest.site_id, "component_id": comp_name},
                    )
                    components_indexed += 1

        logger.info(f"GenerationAgent: successfully completed and indexed {components_indexed} components.")
        return {
            "components_dir": str(components_dir),
            "codegen_res": codegen_res.model_dump(),
            "site_dir": site_dir,
            "indexed_documents": 2 + components_indexed,
            "visual_plan": visual_plan.model_dump(),
        }
