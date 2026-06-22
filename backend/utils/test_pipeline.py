import os
import sys
from pathlib import Path

# Ensure backend can be imported correctly
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from backend.schemas.agents import AgentRunContext
from backend.agents.langgraph_agent import LangGraphAgent
from backend.database.chroma_client import ChromaClientManager
from backend.rag.embeddings import EmbeddingGenerator
from backend.schemas.dataset_builder import DatasetManifest
from backend.utils.custom_logger import setup_logger

logger = setup_logger("utils.test_pipeline")


def run_pipeline_test() -> None:
    logger.info("Initializing Pipeline Integration Test Harness...")

    # Define paths
    base_dir = Path(__file__).resolve().parent.parent.parent
    site_dir = base_dir / "dataset" / "site_000002"

    # Reset site directory from previous runs to ensure clean test
    if site_dir.exists():
        import shutil
        logger.info(f"Removing old dataset directory: {site_dir}")
        shutil.rmtree(site_dir)

    # 1. Instantiate LangGraph Pipeline Agent
    agent = LangGraphAgent()

    # 2. Run Context setup (target site_id 2 via project_id)
    context = AgentRunContext(
        target_framework="React",
        metadata={
            "url": "https://example.com",
            "project_id": "2"
        }
    )

    logger.info("Triggering LangGraph multi-agent pipeline...")
    result = agent.run(context)

    # 3. Log details
    logger.info("------------- Pipeline Execution Results -------------")
    logger.info(f"Execution Success: {result.success}")
    logger.info(f"Execution Status: {result.status}")
    logger.info(f"Audit log message count: {len(result.messages)}")
    for msg in result.messages:
        logger.info(f"[{msg.sender}]: {msg.content}")

    # Assertions
    logger.info("Running validation checks...")
    assert result.success is True, "Pipeline execution failed!"
    assert result.status == "COMPLETED", "Pipeline execution status not COMPLETED!"
    assert len(result.messages) >= 7, "Not all agent nodes were executed!"

    # 4. Verify packaged assets
    assert site_dir.exists(), "Dataset site package directory site_000002 not created!"
    assert (site_dir / "raw_html.html").exists(), "raw_html.html missing from package!"
    assert (site_dir / "screenshot.png").exists(), "screenshot.png missing from package!"
    assert (site_dir / "extraction_result.json").exists(), "extraction_result.json missing from package!"
    assert (site_dir / "vision_metadata.json").exists(), "vision_metadata.json missing from package!"
    assert (site_dir / "layout_analysis.json").exists(), "layout_analysis.json missing from package!"
    assert (site_dir / "manifest.json").exists(), "manifest.json index missing from package!"

    # Verify component subfolder contains generated components
    components_dir = site_dir / "components"
    assert components_dir.exists(), "components subfolder missing!"
    components_files = [f for f in os.listdir(components_dir) if f.endswith(".tsx")]
    assert len(components_files) > 0, "No React components found in components subfolder!"
    logger.info(f"[PASS] Packaged files checked. Found {len(components_files)} components: {components_files}")

    # Load and check manifest details
    with open(site_dir / "manifest.json", "r", encoding="utf-8") as f:
        manifest = DatasetManifest.model_validate_json(f.read())
    assert manifest.site_id == "site_000002", "Manifest site_id mismatch!"
    assert manifest.url == "https://example.com", "Manifest url mismatch!"
    logger.info(f"[PASS] Manifest metadata checked: site_id={manifest.site_id}, components={manifest.components_count}")

    # 5. Verify RAG semantic index
    logger.info("Verifying RAG search against ChromaDB vector index...")
    chroma = ChromaClientManager()
    generator = EmbeddingGenerator()

    query_text = "illustrative examples of domain names"
    query_vector = generator.get_embedding(query_text)

    search_result = chroma.query_similarity(
        collection_name="pages",
        query_vector=query_vector,
        limit=5
    )

    logger.info(f"ChromaDB search matches count: {len(search_result.results)}")
    found = False
    for res in search_result.results:
        logger.info(f"Match: ID={res.id}, Distance={res.distance:.4f}, SiteID={res.metadata.get('site_id')}")
        if res.metadata.get("site_id") == "site_000002":
            found = True

    assert found is True, "The crawled page site_000002 was not found in ChromaDB 'pages' semantic index!"
    logger.info("[PASS] RAG semantic search query check passed.")

    logger.info("ALL PIPELINE INTEGRATION CHECKS PASSED SUCCESSFULLY!")


if __name__ == "__main__":
    run_pipeline_test()
