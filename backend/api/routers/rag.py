from fastapi import APIRouter, HTTPException, status
from backend.rag.service import RAGService
from backend.schemas.rag import RAGQueryRequest, RAGQueryResponse
from backend.utils.custom_logger import setup_logger

logger = setup_logger("api.routers.rag")
router = APIRouter(prefix="/rag", tags=["rag"])


@router.post(
    "/query",
    response_model=RAGQueryResponse,
    status_code=status.HTTP_200_OK,
    summary="Semantic similarity search RAG query",
    description="Vectorizes the prompt, retrieves Top-K closest documents from ChromaDB, and asks the LLM to generate an answer."
)
def query_rag_endpoint(request: RAGQueryRequest) -> RAGQueryResponse:
    logger.info(f"FastAPI: Received RAG query request for prompt: '{request.prompt}'")
    try:
        service = RAGService()
        response = service.query(request)
        return response
    except Exception as e:
        logger.exception(f"FastAPI RAG router error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to execute RAG query semantic synthesis: {str(e)}"
        )
