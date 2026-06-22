from fastapi import APIRouter, Depends, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from backend.database.session import get_db
from backend.utils.custom_logger import setup_logger

logger = setup_logger("api.routers.generation")
router = APIRouter(prefix="/generation", tags=["generation"])

class GenerateRequest(BaseModel):
    project_id: str
    prompt: str

class GenerateResponse(BaseModel):
    execution_id: str
    status: str

class CodegenRequest(BaseModel):
    execution_id: str

class CodegenResponse(BaseModel):
    job_id: str
    status: str

@router.post("/generate", response_model=GenerateResponse, status_code=status.HTTP_202_ACCEPTED)
def start_generation(request: GenerateRequest, db: Session = Depends(get_db)):
    logger.info(f"Received generation request for project {request.project_id} with prompt: {request.prompt}")
    # Mocking generation start, real code will start LangGraph pipeline
    return GenerateResponse(
        execution_id="mock-execution-id-1234",
        status="running"
    )

@router.post("/codegen", response_model=CodegenResponse, status_code=status.HTTP_202_ACCEPTED)
def start_codegen(request: CodegenRequest, db: Session = Depends(get_db)):
    logger.info(f"Received codegen request for execution {request.execution_id}")
    # Mocking codegen start
    return CodegenResponse(
        job_id="mock-job-id-codegen",
        status="processing"
    )
