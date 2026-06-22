from fastapi import APIRouter, Depends, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from backend.database.session import get_db
from backend.utils.custom_logger import setup_logger

logger = setup_logger("api.routers.dataset")
router = APIRouter(prefix="/dataset", tags=["dataset"])

class DatasetRegisterRequest(BaseModel):
    project_id: str
    url: str

class DatasetRegisterResponse(BaseModel):
    dataset_id: str
    status: str

@router.post("/dataset", response_model=DatasetRegisterResponse, status_code=status.HTTP_201_CREATED)
def register_dataset(request: DatasetRegisterRequest, db: Session = Depends(get_db)):
    logger.info(f"Registering dataset for url {request.url} in project {request.project_id}")
    # Mocking dataset entry creation
    return DatasetRegisterResponse(
        dataset_id="mock-dataset-id-5678",
        status="registered"
    )
