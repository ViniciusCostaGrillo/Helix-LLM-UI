import sys
from pathlib import Path

# Ensure backend can be imported correctly
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from fastapi.testclient import TestClient
from backend.api.main import app
from backend.database.chroma_client import ChromaClientManager
from backend.rag.embeddings import EmbeddingGenerator
from backend.rag.service import RAGService
from backend.schemas.rag import RAGQueryRequest
from backend.utils.custom_logger import setup_logger

logger = setup_logger("utils.test_rag")


def run_tests() -> None:
    logger.info("Initializing FASE 20 RAG Compilation and Integration Test Harness...")

    chroma = ChromaClientManager()
    generator = EmbeddingGenerator()

    # 1. Seed ChromaDB Collections with Test Data
    logger.info("Seeding ChromaDB collections with test layout data...")

    # A. Page details document
    page_id = "site_rag_test_999"
    page_text = "Standard Admin Dashboard page layout containing a sidebar menu, search header, data cards grid, and dark theme colors."
    page_vector = generator.get_embedding(page_text)
    chroma.upsert(
        collection_name="pages",
        doc_id=page_id,
        vector=page_vector,
        document=page_text,
        metadata={"site_id": page_id, "url": "https://rag-test-dashboard.com"}
    )

    # B. Component code document
    comp_id = f"{page_id}_Sidebar"
    comp_code = (
        "import React from 'react';\n"
        "export default function Sidebar() {\n"
        "  return (\n"
        "    <aside className=\"w-64 h-screen bg-gray-900 text-slate-100 flex flex-col\">\n"
        "      <div className=\"p-4 text-xl font-bold border-b border-gray-800\">AdminPanel</div>\n"
        "      <nav className=\"flex-1 p-2 space-y-1\">\n"
        "        <a href=\"#\" className=\"block px-4 py-2 rounded bg-gray-800\">Dashboard</a>\n"
        "        <a href=\"#\" className=\"block px-4 py-2 rounded hover:bg-gray-800\">Settings</a>\n"
        "      </nav>\n"
        "    </aside>\n"
        "  );\n"
        "}"
    )
    comp_vector = generator.get_embedding(comp_code)
    chroma.upsert(
        collection_name="components",
        doc_id=comp_id,
        vector=comp_vector,
        document=comp_code,
        metadata={"site_id": page_id, "component_id": "Sidebar"}
    )

    # C. Design styles document
    style_text = "Design Palette: Primary: emerald-600, Secondary: slate-800, Background: dark-gray. Font: Inter. Spacing profile: default margins."
    style_vector = generator.get_embedding(style_text)
    chroma.upsert(
        collection_name="styles",
        doc_id=page_id,
        vector=style_vector,
        document=style_text,
        metadata={"site_id": page_id}
    )

    logger.info("[PASS] Successfully seeded pages, components, and styles collections.")

    # 2. Test RAG Service Query execution
    logger.info("Executing RAG service query lookup...")
    service = RAGService()

    # Query for dashboard sidebar bg-gray-900
    req = RAGQueryRequest(
        prompt="dashboard sidebar components styled with bg-gray-900 and emerald-600 background",
        limit=3
    )
    res = service.query(req)

    assert res.prompt == req.prompt, "Response prompt mismatch!"
    assert len(res.retrieved_contexts) > 0, "No documents were retrieved!"
    assert res.answer is not None and len(res.answer) > 0, "RAG answer is empty!"

    # Print out results for verification
    logger.info("------------- RAG Service Output -------------")
    logger.info(f"Prompt: {res.prompt}")
    logger.info(f"Retrieved matched contexts: {len(res.retrieved_contexts)}")
    for doc in res.retrieved_contexts:
        logger.info(f" - Collection: '{doc.collection}', ID: '{doc.id}', Distance: {doc.distance:.4f}")
    logger.info(f"Generated RAG Synthesis Response:\n{res.answer}")
    logger.info("---------------------------------------------")

    logger.info("[PASS] RAG service semantic query execution passed.")

    # 3. Validate RAG FastAPI routing using TestClient
    logger.info("Validating RAG Router HTTP endpoints via TestClient...")
    client = TestClient(app)

    payload = {
        "prompt": "Show me admin dashboard palette with dark theme style spacing profile",
        "limit": 2
    }
    http_res = client.post("/rag/query", json=payload)
    
    assert http_res.status_code == 200, f"RAG API query failed with status {http_res.status_code}: {http_res.text}"
    
    data = http_res.json()
    assert "prompt" in data and data["prompt"] == payload["prompt"], "API response prompt mismatch!"
    assert "answer" in data and len(data["answer"]) > 0, "API response answer empty!"
    assert "retrieved_contexts" in data and len(data["retrieved_contexts"]) > 0, "API response retrieved context empty!"
    
    logger.info("------------- RAG Router HTTP Output -------------")
    logger.info(f"Status: {http_res.status_code}")
    logger.info(f"Retrieved: {len(data['retrieved_contexts'])} items")
    logger.info(f"Answer Sample: {data['answer'][:200]}...")
    logger.info("--------------------------------------------------")

    logger.info("[PASS] RAG router HTTP API validation checks passed.")
    logger.info("ALL FASE 20 RAG INTEGRATION CHECKS PASSED SUCCESSFULLY!")


if __name__ == "__main__":
    run_tests()
