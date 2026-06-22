import os
import logging
import asyncio
from typing import Dict, Any, List, TypedDict
from pathlib import Path

import nest_asyncio
from langgraph.graph import StateGraph, END

from backend.schemas.agents import AgentMessage, AgentRunContext, AgentRunResult

logger = logging.getLogger(__name__)


def run_async_coro(coro):
    """Utility to run an async coroutine inside a synchronous node context,
    supporting nested loops via nest_asyncio.
    """
    try:
        loop = asyncio.get_running_loop()
        nest_asyncio.apply(loop)
        return loop.run_until_complete(coro)
    except RuntimeError:
        return asyncio.run(coro)


class PipelineState(TypedDict):
    messages: List[AgentMessage]
    context: AgentRunContext
    current_node: str
    outputs: Dict[str, Any]
    errors: List[str]


class LangGraphAgent:
    def __init__(self):
        self.workflow = StateGraph(PipelineState)
        self._build_graph()
        self.compiled_graph = self.workflow.compile()

    def _build_graph(self):
        # Define nodes
        self.workflow.add_node("crawler", self.crawler_node)
        self.workflow.add_node("extractor", self.extractor_node)
        self.workflow.add_node("vision", self.vision_node)
        self.workflow.add_node("style", self.style_node)
        self.workflow.add_node("code", self.code_node)
        self.workflow.add_node("dataset", self.dataset_node)
        self.workflow.add_node("rag", self.rag_node)

        # Define progression (routing)
        self.workflow.set_entry_point("crawler")
        self.workflow.add_edge("crawler", "extractor")
        self.workflow.add_edge("extractor", "vision")
        self.workflow.add_edge("vision", "style")
        self.workflow.add_edge("style", "code")
        self.workflow.add_edge("code", "dataset")
        self.workflow.add_edge("dataset", "rag")
        self.workflow.add_edge("rag", END)

    def crawler_node(self, state: PipelineState) -> Dict[str, Any]:
        logger.info("LangGraph: executing crawler node")
        context = state.get("context")
        
        # Decide url
        url = context.metadata.get("url") or "https://example.com"
        
        # Output directory
        base_dir = Path(__file__).resolve().parent.parent.parent
        output_dir = base_dir / "storage" / "pipeline" / "run_latest"
        os.makedirs(output_dir, exist_ok=True)
        
        # Instantiate PlaywrightEngine
        from backend.crawler.playwright_engine import PlaywrightEngine
        crawler = PlaywrightEngine()
        
        try:
            # Execute async crawl synchronously
            crawl_res = run_async_coro(crawler.crawl(url, str(output_dir)))
            html_path = crawl_res["html_path"]
            screenshot_path = crawl_res["screenshot_path"]
            
            with open(html_path, "r", encoding="utf-8") as f:
                html_content = f.read()
                
            msg = AgentMessage(
                sender="CrawlerAgent",
                content=f"Crawled target URL {url} successfully. HTML and screenshot captured."
            )
            crawler_data = {
                "html_path": str(html_path),
                "screenshot_path": str(screenshot_path),
                "html_content": html_content,
                "url": url,
                "status": "success"
            }
        except Exception as e:
            logger.exception(f"Crawler node failed: {e}")
            msg = AgentMessage(
                sender="CrawlerAgent",
                content=f"Crawling failed: {str(e)}. Falling back to mock assets."
            )
            
            # fallback mock assets
            mock_html = (
                "<!DOCTYPE html><html><head><title>Example Domain</title></head><body>"
                "<div class='container'><header class='header'>Example Header</header>"
                "<main class='content'><h1>Example Domain</h1><p>This domain is for use in illustrative examples.</p>"
                "<a href='https://www.iana.org/domains/reserved'>More information...</a></main></div>"
                "</body></html>"
            )
            
            # Save mock HTML
            html_path = output_dir / "page.html"
            with open(html_path, "w", encoding="utf-8") as f:
                f.write(mock_html)
                
            mock_screenshot = output_dir / "screenshot.png"
            if not mock_screenshot.exists():
                from PIL import Image
                img = Image.new('RGB', (100, 100), color='blue')
                img.save(mock_screenshot)
                
            crawler_data = {
                "html_path": str(html_path),
                "screenshot_path": str(mock_screenshot),
                "html_content": mock_html,
                "url": url,
                "status": "mock_fallback"
            }
            
        new_messages = list(state.get("messages", [])) + [msg]
        new_outputs = dict(state.get("outputs", {}))
        new_outputs["crawler_data"] = crawler_data
        
        return {
            "messages": new_messages,
            "current_node": "crawler",
            "outputs": new_outputs
        }

    def extractor_node(self, state: PipelineState) -> Dict[str, Any]:
        logger.info("LangGraph: executing extractor node")
        crawler_data = state["outputs"].get("crawler_data", {})
        html_content = crawler_data.get("html_content") or ""
        
        from backend.extractor.service import ExtractorService
        extractor = ExtractorService()
        
        try:
            result = extractor.extract(html_content)
            msg = AgentMessage(
                sender="ExtractorAgent",
                content="Extracted semantic components, metadata headers, and styles from raw HTML."
            )
            
            # Save extraction result to file to replicate phase behavior
            base_dir = Path(__file__).resolve().parent.parent.parent
            output_dir = base_dir / "storage" / "pipeline" / "run_latest"
            os.makedirs(output_dir, exist_ok=True)
            extraction_path = output_dir / "extraction_result.json"
            with open(extraction_path, "w", encoding="utf-8") as f:
                f.write(result.model_dump_json(indent=2))
                
            extractor_data = {
                "result": result.model_dump(),
                "extraction_result_path": str(extraction_path),
                "status": "success"
            }
        except Exception as e:
            logger.exception(f"Extractor node failed: {e}")
            msg = AgentMessage(
                sender="ExtractorAgent",
                content=f"Extraction failed: {str(e)}."
            )
            extractor_data = {"status": "error", "error": str(e)}
            
        new_messages = list(state.get("messages", [])) + [msg]
        new_outputs = dict(state.get("outputs", {}))
        new_outputs["extractor_data"] = extractor_data
        return {
            "messages": new_messages,
            "current_node": "extractor",
            "outputs": new_outputs
        }

    def vision_node(self, state: PipelineState) -> Dict[str, Any]:
        logger.info("LangGraph: executing vision node")
        crawler_data = state["outputs"].get("crawler_data", {})
        screenshot_path = crawler_data.get("screenshot_path")
        
        from backend.vision.analyzer import VisionAnalyzer
        analyzer = VisionAnalyzer()
        
        try:
            result = analyzer.analyze(str(screenshot_path))
            msg = AgentMessage(
                sender="VisionAgent",
                content="Processed screenshot visual grids, colors, and active spaces."
            )
            
            # Save vision metadata to file
            base_dir = Path(__file__).resolve().parent.parent.parent
            output_dir = base_dir / "storage" / "pipeline" / "run_latest"
            os.makedirs(output_dir, exist_ok=True)
            vision_path = output_dir / "vision_metadata.json"
            with open(vision_path, "w", encoding="utf-8") as f:
                f.write(result.model_dump_json(indent=2))
                
            vision_data = {
                "result": result.model_dump(),
                "vision_metadata_path": str(vision_path),
                "status": "success"
            }
        except Exception as e:
            logger.exception(f"Vision node failed: {e}")
            msg = AgentMessage(
                sender="VisionAgent",
                content=f"Visual analysis failed: {str(e)}."
            )
            vision_data = {"status": "error", "error": str(e)}
            
        new_messages = list(state.get("messages", [])) + [msg]
        new_outputs = dict(state.get("outputs", {}))
        new_outputs["vision_data"] = vision_data
        return {
            "messages": new_messages,
            "current_node": "vision",
            "outputs": new_outputs
        }

    def style_node(self, state: PipelineState) -> Dict[str, Any]:
        logger.info("LangGraph: executing style node")
        
        from backend.schemas.extractor import ExtractionResult
        from backend.schemas.vision import VisionMetadata
        from backend.analyzer.layout_analyzer import LayoutAnalyzer
        
        extractor_out = state["outputs"].get("extractor_data", {})
        vision_out = state["outputs"].get("vision_data", {})
        
        try:
            extraction = ExtractionResult.model_validate(extractor_out["result"])
            vision = VisionMetadata.model_validate(vision_out["result"])
            
            analyzer = LayoutAnalyzer()
            result = analyzer.analyze(extraction, vision)
            
            msg = AgentMessage(
                sender="StyleAgent",
                content="Resolved visual layout design guidelines and theme palette tokens."
            )
            
            # Save analysis metadata to file
            base_dir = Path(__file__).resolve().parent.parent.parent
            output_dir = base_dir / "storage" / "pipeline" / "run_latest"
            os.makedirs(output_dir, exist_ok=True)
            analysis_path = output_dir / "metadata.json"
            with open(analysis_path, "w", encoding="utf-8") as f:
                f.write(result.model_dump_json(indent=2))
                
            style_data = {
                "result": result.model_dump(),
                "analysis_path": str(analysis_path),
                "status": "success"
            }
        except Exception as e:
            logger.exception(f"Style node failed: {e}")
            msg = AgentMessage(
                sender="StyleAgent",
                content=f"Style layout analysis failed: {str(e)}."
            )
            style_data = {"status": "error", "error": str(e)}
            
        new_messages = list(state.get("messages", [])) + [msg]
        new_outputs = dict(state.get("outputs", {}))
        new_outputs["style_data"] = style_data
        return {
            "messages": new_messages,
            "current_node": "style",
            "outputs": new_outputs
        }

    def code_node(self, state: PipelineState) -> Dict[str, Any]:
        logger.info("LangGraph: executing code node")
        
        from backend.schemas.extractor import ExtractionResult
        from backend.schemas.analyzer import AnalysisResult
        from backend.codegen.code_generator import CodeGenerator
        
        extractor_out = state["outputs"].get("extractor_data", {})
        style_out = state["outputs"].get("style_data", {})
        
        try:
            extraction = ExtractionResult.model_validate(extractor_out["result"])
            analysis = AnalysisResult.model_validate(style_out["result"])
            
            generator = CodeGenerator()
            result = generator.generate(extraction, analysis)
            
            msg = AgentMessage(
                sender="CodeAgent",
                content="Generated React + Tailwind CSS code components from layout patterns."
            )
            
            # Save components to filesystem
            base_dir = Path(__file__).resolve().parent.parent.parent
            output_dir = base_dir / "storage" / "pipeline" / "run_latest"
            components_dir = output_dir / "components"
            os.makedirs(components_dir, exist_ok=True)
            
            for comp in result.components:
                comp_file = components_dir / f"{comp.name}.tsx"
                with open(comp_file, "w", encoding="utf-8") as cf:
                    cf.write(comp.code)
                    
            if result.global_styles:
                styles_file = output_dir / "global_styles.css"
                with open(styles_file, "w", encoding="utf-8") as sf:
                    sf.write(result.global_styles)
                    
            code_data = {
                "result": result.model_dump(),
                "components_dir": str(components_dir),
                "status": "success"
            }
        except Exception as e:
            logger.exception(f"Code node failed: {e}")
            msg = AgentMessage(
                sender="CodeAgent",
                content=f"Code generation failed: {str(e)}."
            )
            code_data = {"status": "error", "error": str(e)}
            
        new_messages = list(state.get("messages", [])) + [msg]
        new_outputs = dict(state.get("outputs", {}))
        new_outputs["code_data"] = code_data
        return {
            "messages": new_messages,
            "current_node": "code",
            "outputs": new_outputs
        }

    def dataset_node(self, state: PipelineState) -> Dict[str, Any]:
        logger.info("LangGraph: executing dataset node")
        
        from backend.schemas.extractor import ExtractionResult
        from backend.schemas.vision import VisionMetadata
        from backend.schemas.analyzer import AnalysisResult
        from backend.schemas.codegen import CodegenResult
        from backend.dataset.builder import DatasetBuilder
        
        crawler_out = state["outputs"].get("crawler_data", {})
        extractor_out = state["outputs"].get("extractor_data", {})
        vision_out = state["outputs"].get("vision_data", {})
        style_out = state["outputs"].get("style_data", {})
        code_out = state["outputs"].get("code_data", {})
        context = state.get("context")
        
        try:
            # Reconstruct models
            extraction = ExtractionResult.model_validate(extractor_out["result"])
            vision = VisionMetadata.model_validate(vision_out["result"])
            analysis = AnalysisResult.model_validate(style_out["result"])
            codegen = CodegenResult.model_validate(code_out["result"])
            
            project_id = context.metadata.get("project_id", 1)
            site_id = int(project_id)
            
            base_dir = Path(__file__).resolve().parent.parent.parent
            builder = DatasetBuilder(base_dataset_path=str(base_dir / "dataset"))
            
            # Extract raw html and screenshot path
            raw_html = crawler_out.get("html_content") or ""
            screenshot_path = crawler_out.get("screenshot_path")
            
            site_dir = builder.build_package(
                site_id=site_id,
                url=crawler_out.get("url", "https://example.com"),
                raw_html=raw_html,
                screenshot_path=screenshot_path,
                extraction=extraction,
                vision=vision,
                analysis=analysis,
                codegen=codegen
            )
            
            msg = AgentMessage(
                sender="DatasetAgent",
                content=f"Packaged crawled resources and React source modules into dataset package: {site_dir}"
            )
            
            dataset_data = {
                "site_dir": site_dir,
                "status": "success"
            }
        except Exception as e:
            logger.exception(f"Dataset node failed: {e}")
            msg = AgentMessage(
                sender="DatasetAgent",
                content=f"Dataset package compilation failed: {str(e)}."
            )
            dataset_data = {"status": "error", "error": str(e)}
            
        new_messages = list(state.get("messages", [])) + [msg]
        new_outputs = dict(state.get("outputs", {}))
        new_outputs["dataset_data"] = dataset_data
        return {
            "messages": new_messages,
            "current_node": "dataset",
            "outputs": new_outputs
        }

    def rag_node(self, state: PipelineState) -> Dict[str, Any]:
        logger.info("LangGraph: executing rag node")
        
        from backend.database.chroma_client import ChromaClientManager
        from backend.rag.embeddings import EmbeddingGenerator
        from backend.schemas.dataset_builder import DatasetManifest
        
        dataset_out = state["outputs"].get("dataset_data", {})
        
        try:
            site_dir = dataset_out.get("site_dir")
            if not site_dir:
                raise ValueError("Dataset packaging directory not found")
                
            site_path = Path(site_dir)
            manifest_path = site_path / "manifest.json"
            
            # Load manifest
            with open(manifest_path, "r", encoding="utf-8") as f:
                manifest = DatasetManifest.model_validate_json(f.read())
                
            generator = EmbeddingGenerator()
            chroma = ChromaClientManager()
            
            page_text = f"Page layout for {manifest.site_id} crawled from {manifest.url}. Primary color: {manifest.primary_color}, Background: {manifest.background_color}."
            page_vector = generator.get_embedding(page_text)
            
            chroma.upsert(
                collection_name="pages",
                doc_id=manifest.site_id,
                vector=page_vector,
                document=page_text,
                metadata={"url": manifest.url, "site_id": manifest.site_id}
            )
            
            # Index style vector
            logger.info("Indexing style visual tokens into ChromaDB...")
            style_text = f"Theme palette. Primary: {manifest.primary_color}, Background: {manifest.background_color}"
            style_vector = generator.get_embedding(style_text)
            
            chroma.upsert(
                collection_name="styles",
                doc_id=manifest.site_id,
                vector=style_vector,
                document=style_text,
                metadata={"site_id": manifest.site_id}
            )
            
            # Index components vectors
            components_path = site_path / "components"
            components_indexed = 0
            if components_path.exists():
                for file in os.listdir(components_path):
                    if file.endswith(".tsx"):
                        comp_name = file.replace(".tsx", "")
                        comp_file = components_path / file
                        with open(comp_file, "r", encoding="utf-8") as cf:
                            comp_code = cf.read()
                        
                        comp_vector = generator.get_embedding(comp_code)
                        doc_id = f"{manifest.site_id}_{comp_name}"
                        
                        chroma.upsert(
                            collection_name="components",
                            doc_id=doc_id,
                            vector=comp_vector,
                            document=comp_code,
                            metadata={"site_id": manifest.site_id, "component_id": comp_name}
                        )
                        components_indexed += 1
            
            msg = AgentMessage(
                sender="RagAgent",
                content=f"Computed dense semantic vectors. Upserted layout details and {components_indexed} components to ChromaDB collections."
            )
            rag_data = {
                "indexed_documents": 2 + components_indexed,
                "status": "success"
            }
        except Exception as e:
            logger.exception(f"Rag node failed: {e}")
            msg = AgentMessage(
                sender="RagAgent",
                content=f"RAG semantic indexing failed: {str(e)}."
            )
            rag_data = {"status": "error", "error": str(e)}
            
        new_messages = list(state.get("messages", [])) + [msg]
        new_outputs = dict(state.get("outputs", {}))
        new_outputs["rag_data"] = rag_data
        return {
            "messages": new_messages,
            "current_node": "rag",
            "outputs": new_outputs
        }

    def run(self, context: AgentRunContext) -> AgentRunResult:
        initial_state: PipelineState = {
            "messages": [],
            "context": context,
            "current_node": "entry",
            "outputs": {},
            "errors": []
        }
        try:
            final_state = self.compiled_graph.invoke(initial_state)
            errors = final_state.get("errors", [])
            success = len(errors) == 0
            status = "COMPLETED" if success else "FAILED"
            return AgentRunResult(
                success=success,
                status=status,
                messages=final_state.get("messages", []),
                output_data=final_state.get("outputs", {}),
                metadata={"langgraph_execution": True}
            )
        except Exception as e:
            logger.exception("Failed to run LangGraph multi-agent pipeline")
            error_msg = AgentMessage(
                sender="LangGraphEngine",
                content=f"Error executing graph pipeline: {str(e)}"
            )
            return AgentRunResult(
                success=False,
                status="ERROR",
                messages=[error_msg],
                output_data={},
                metadata={"error": str(e)}
            )
