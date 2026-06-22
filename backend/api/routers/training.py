from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.database.models import TrainingHistory
from backend.database.session import get_db, SessionLocal
from backend.schemas.training import (
    TrainingHistoryCreate,
    TrainingHistoryResponse,
)
from backend.training.service import TrainingOrchestrationService
from backend.utils.custom_logger import setup_logger

logger = setup_logger("api.routers.training")
router = APIRouter(prefix="/training", tags=["training"])


@router.post(
    "/start",
    response_model=TrainingHistoryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Trigger model fine-tuning training job",
    description="Compiles datasets, generates SFT formatting maps, and starts model training adapters optimization in the background."
)
def start_model_training(
    request: TrainingHistoryCreate,
    db: Session = Depends(get_db)
) -> TrainingHistoryResponse:
    logger.info(f"FastAPI: Received training request. Model: {request.model_name}, Base: {request.base_model}")
    
    try:
        # Create DB record representing this training job
        job = TrainingHistory(
            model_name=request.model_name,
            base_model=request.base_model,
            dataset_path=request.dataset_path,
            epochs=request.epochs,
            status="pending"
        )
        db.add(job)
        db.commit()
        db.refresh(job)
        
        # Trigger background training thread
        service = TrainingOrchestrationService()
        service.start_training(job.id, SessionLocal)
        
        logger.info(f"FastAPI: Training job triggered successfully. JobID: {job.id}")
        return TrainingHistoryResponse.model_validate(job)
        
    except Exception as e:
        logger.exception(f"FastAPI start training endpoint failure: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to initialize model fine-tuning job execution context: {str(e)}"
        )


@router.get(
    "/status/{job_id}",
    response_model=TrainingHistoryResponse,
    status_code=status.HTTP_200_OK,
    summary="Get model training status",
    description="Queries the relational database to fetch current epoch loss progression, runtime state logs, or errors."
)
def get_training_job_status(
    job_id: str,
    db: Session = Depends(get_db)
) -> TrainingHistoryResponse:
    logger.info(f"FastAPI: Querying status for training job ID: {job_id}")
    job = db.query(TrainingHistory).filter(TrainingHistory.id == job_id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Training job {job_id} not found in database history records."
        )
    return TrainingHistoryResponse.model_validate(job)


@router.get(
    "/history",
    response_model=List[TrainingHistoryResponse],
    status_code=status.HTTP_200_OK,
    summary="List training jobs history runs",
    description="Retrieves a complete list of past and running fine-tuning executions from the database."
)
def list_training_history_jobs(
    db: Session = Depends(get_db)
) -> List[TrainingHistoryResponse]:
    logger.info("FastAPI: Retrieving training jobs history list...")
    jobs = db.query(TrainingHistory).order_by(TrainingHistory.created_at.desc()).all()
    return [TrainingHistoryResponse.model_validate(j) for j in jobs]
