import os
import logging
from datetime import datetime, timedelta
from pathlib import Path

from airflow import DAG
from airflow.providers.standard.operators.python import PythonOperator

logger = logging.getLogger("airflow.task")


def run_async_coro(coro):
    """Run an async coroutine synchronously inside the Airflow worker."""
    import asyncio
    import nest_asyncio
    try:
        loop = asyncio.get_running_loop()
        nest_asyncio.apply(loop)
        return loop.run_until_complete(coro)
    except RuntimeError:
        return asyncio.run(coro)


def crawl_page_fn(**context) -> dict:
    """Airflow Task: Headless browser crawling and screenshot capture."""
    # Retrieve target URL or default
    conf = context.get("dag_run").conf or {}
    url = conf.get("url") or "https://example.com"
    
    base_dir = Path(__file__).resolve().parent.parent.parent
    output_dir = base_dir / "storage" / "airflow_run"
    os.makedirs(output_dir, exist_ok=True)
    
    logger.info(f"Starting crawl task for URL: {url}...")
    from backend.crawler.playwright_engine import PlaywrightEngine
    crawler = PlaywrightEngine()
    
    try:
        crawl_res = run_async_coro(crawler.crawl(url, str(output_dir)))
        html_path = crawl_res["html_path"]
        screenshot_path = crawl_res["screenshot_path"]
        
        with open(html_path, "r", encoding="utf-8") as f:
            html_content = f.read()
            
        return {
            "html_path": str(html_path),
            "screenshot_path": str(screenshot_path),
            "html_content": html_content,
            "url": url,
            "status": "success"
        }
    except Exception as e:
        logger.exception(f"Crawl failed: {e}. Generating mock assets.")
        mock_html = (
            "<!DOCTYPE html><html><body>"
            "<div class='container'><h1>Airflow Batch Processing</h1>"
            "<p>Orchestrated layout via Airflow PythonOperators.</p>"
            "</div></body></html>"
        )
        html_path = output_dir / "page.html"
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(mock_html)
            
        mock_screenshot = output_dir / "screenshot.png"
        if not mock_screenshot.exists():
            from PIL import Image
            img = Image.new('RGB', (100, 100), color='purple')
            img.save(mock_screenshot)
            
        return {
            "html_path": str(html_path),
            "screenshot_path": str(mock_screenshot),
            "html_content": mock_html,
            "url": url,
            "status": "mock_fallback"
        }


def extract_content_fn(**context) -> dict:
    """Airflow Task: Structure extractor for DOM components and styles."""
    ti = context["task_instance"]
    crawl_res = ti.xcom_pull(task_ids="crawl_page")
    html_content = crawl_res.get("html_content") or ""
    
    from backend.extractor.service import ExtractorService
    extractor = ExtractorService()
    result = extractor.extract(html_content)
    
    base_dir = Path(__file__).resolve().parent.parent.parent
    output_dir = base_dir / "storage" / "airflow_run"
    os.makedirs(output_dir, exist_ok=True)
    extraction_path = output_dir / "extraction_result.json"
    with open(extraction_path, "w", encoding="utf-8") as f:
        f.write(result.model_dump_json(indent=2))
        
    return {
        "result": result.model_dump(),
        "extraction_result_path": str(extraction_path)
    }


def analyze_visuals_fn(**context) -> dict:
    """Airflow Task: Image processor for visual grids, density, and color spaces."""
    ti = context["task_instance"]
    crawl_res = ti.xcom_pull(task_ids="crawl_page")
    screenshot_path = crawl_res.get("screenshot_path")
    
    from backend.vision.analyzer import VisionAnalyzer
    analyzer = VisionAnalyzer()
    result = analyzer.analyze(screenshot_path)
    
    base_dir = Path(__file__).resolve().parent.parent.parent
    output_dir = base_dir / "storage" / "airflow_run"
    os.makedirs(output_dir, exist_ok=True)
    vision_path = output_dir / "vision_metadata.json"
    with open(vision_path, "w", encoding="utf-8") as f:
        f.write(result.model_dump_json(indent=2))
        
    return {
        "result": result.model_dump(),
        "vision_metadata_path": str(vision_path)
    }


def resolve_styles_fn(**context) -> dict:
    """Airflow Task: Layout guidelines analysis from extracted styles and grids."""
    ti = context["task_instance"]
    extractor_res = ti.xcom_pull(task_ids="extract_content")
    vision_res = ti.xcom_pull(task_ids="analyze_visuals")
    
    from backend.schemas.extractor import ExtractionResult
    from backend.schemas.vision import VisionMetadata
    from backend.analyzer.layout_analyzer import LayoutAnalyzer
    
    extraction = ExtractionResult.model_validate(extractor_res["result"])
    vision = VisionMetadata.model_validate(vision_res["result"])
    
    analyzer = LayoutAnalyzer()
    result = analyzer.analyze(extraction, vision)
    
    base_dir = Path(__file__).resolve().parent.parent.parent
    output_dir = base_dir / "storage" / "airflow_run"
    os.makedirs(output_dir, exist_ok=True)
    analysis_path = output_dir / "metadata.json"
    with open(analysis_path, "w", encoding="utf-8") as f:
        f.write(result.model_dump_json(indent=2))
        
    return {
        "result": result.model_dump(),
        "analysis_path": str(analysis_path)
    }


def generate_code_fn(**context) -> dict:
    """Airflow Task: React components TSX code generation."""
    ti = context["task_instance"]
    extractor_res = ti.xcom_pull(task_ids="extract_content")
    style_res = ti.xcom_pull(task_ids="resolve_styles")
    
    from backend.schemas.extractor import ExtractionResult
    from backend.schemas.analyzer import AnalysisResult
    from backend.codegen.code_generator import CodeGenerator
    
    extraction = ExtractionResult.model_validate(extractor_res["result"])
    analysis = AnalysisResult.model_validate(style_res["result"])
    
    generator = CodeGenerator()
    result = generator.generate(extraction, analysis)
    
    base_dir = Path(__file__).resolve().parent.parent.parent
    output_dir = base_dir / "storage" / "airflow_run"
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
            
    return {
        "result": result.model_dump(),
        "components_dir": str(components_dir)
    }


def package_dataset_fn(**context) -> str:
    """Airflow Task: Package layout design schemas and generated modules."""
    ti = context["task_instance"]
    crawl_res = ti.xcom_pull(task_ids="crawl_page")
    extractor_res = ti.xcom_pull(task_ids="extract_content")
    vision_res = ti.xcom_pull(task_ids="analyze_visuals")
    style_res = ti.xcom_pull(task_ids="resolve_styles")
    codegen_res = ti.xcom_pull(task_ids="generate_code")
    
    # Retrieve project ID or default to 5 (creates site_000005)
    conf = context.get("dag_run").conf or {}
    project_id = int(conf.get("project_id") or 5)
    
    from backend.schemas.extractor import ExtractionResult
    from backend.schemas.vision import VisionMetadata
    from backend.schemas.analyzer import AnalysisResult
    from backend.schemas.codegen import CodegenResult
    from backend.dataset.builder import DatasetBuilder
    
    extraction = ExtractionResult.model_validate(extractor_res["result"])
    vision = VisionMetadata.model_validate(vision_res["result"])
    analysis = AnalysisResult.model_validate(style_res["result"])
    codegen = CodegenResult.model_validate(codegen_res["result"])
    
    base_dir = Path(__file__).resolve().parent.parent.parent
    builder = DatasetBuilder(base_dataset_path=str(base_dir / "dataset"))
    
    site_dir = builder.build_package(
        site_id=project_id,
        url=crawl_res.get("url", "https://example.com"),
        raw_html=crawl_res.get("html_content", ""),
        screenshot_path=crawl_res.get("screenshot_path"),
        extraction=extraction,
        vision=vision,
        analysis=analysis,
        codegen=codegen
    )
    return site_dir


def index_vectors_fn(**context) -> dict:
    """Airflow Task: Index layouts and generated components into ChromaDB collections."""
    ti = context["task_instance"]
    site_dir = ti.xcom_pull(task_ids="package_dataset")
    
    from backend.database.chroma_client import ChromaClientManager
    from backend.rag.embeddings import EmbeddingGenerator
    from backend.schemas.dataset_builder import DatasetManifest
    
    site_path = Path(site_dir)
    manifest_path = site_path / "manifest.json"
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = DatasetManifest.model_validate_json(f.read())
        
    generator = EmbeddingGenerator()
    chroma = ChromaClientManager()
    
    # 1. Page text
    page_text = (
        f"Page layout for {manifest.site_id} crawled from {manifest.url}. "
        f"Primary color: {manifest.primary_color}, Background: {manifest.background_color}."
    )
    page_vector = generator.get_embedding(page_text)
    chroma.upsert(
        collection_name="pages",
        doc_id=manifest.site_id,
        vector=page_vector,
        document=page_text,
        metadata={"url": manifest.url, "site_id": manifest.site_id}
    )
    
    # 2. Style text
    style_text = f"Theme palette. Primary: {manifest.primary_color}, Background: {manifest.background_color}"
    style_vector = generator.get_embedding(style_text)
    chroma.upsert(
        collection_name="styles",
        doc_id=manifest.site_id,
        vector=style_vector,
        document=style_text,
        metadata={"site_id": manifest.site_id}
    )
    
    # 3. Components
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
                
    return {"indexed_documents": 2 + components_indexed}


# Airflow DAG definition
default_args = {
    "owner": "ui_ai_ecosystem",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    dag_id="ui_ai_daily_generation_pipeline",
    default_args=default_args,
    description="Daily pipeline for crawling, layout analysis, and semantic code generation",
    schedule=timedelta(days=1),
    start_date=datetime(2026, 6, 22),
    catchup=False,
) as dag:
    
    crawl_task = PythonOperator(
        task_id="crawl_page",
        python_callable=crawl_page_fn,
    )
    
    extract_task = PythonOperator(
        task_id="extract_content",
        python_callable=extract_content_fn,
    )
    
    vision_task = PythonOperator(
        task_id="analyze_visuals",
        python_callable=analyze_visuals_fn,
    )
    
    style_task = PythonOperator(
        task_id="resolve_styles",
        python_callable=resolve_styles_fn,
    )
    
    codegen_task = PythonOperator(
        task_id="generate_code",
        python_callable=generate_code_fn,
    )
    
    dataset_task = PythonOperator(
        task_id="package_dataset",
        python_callable=package_dataset_fn,
    )
    
    rag_task = PythonOperator(
        task_id="index_vectors",
        python_callable=index_vectors_fn,
    )
    
    # DAG Task dependencies layout
    crawl_task >> extract_task >> vision_task >> style_task >> codegen_task >> dataset_task >> rag_task
