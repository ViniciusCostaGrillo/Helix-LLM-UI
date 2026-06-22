from fastapi import APIRouter, Depends, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from backend.database.session import get_db
from backend.utils.custom_logger import setup_logger

logger = setup_logger("api.routers.analyzer")
router = APIRouter(prefix="/analyzer", tags=["analyzer"])

class AnalyzeRequest(BaseModel):
    dataset_id: str
    execution_id: str

class AnalyzeResponse(BaseModel):
    job_id: str
    status: str

@router.post("/analyze", response_model=AnalyzeResponse, status_code=status.HTTP_202_ACCEPTED)
def start_analyze(request: AnalyzeRequest, db: Session = Depends(get_db)):
    logger.info(f"Received analyze request for dataset {request.dataset_id} in execution {request.execution_id}")
    # Mocking analysis task start
    return AnalyzeResponse(
        job_id="mock-job-id-analyzer",
        status="processing"
    )
