from fastapi import APIRouter, Depends, status
from typing import List, Optional
from pydantic import BaseModel
from sqlalchemy.orm import Session
from backend.database.session import get_db
from backend.utils.custom_logger import setup_logger

logger = setup_logger("api.routers.projects")
router = APIRouter(prefix="/projects", tags=["projects"])

class ProjectItem(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    user_id: str

@router.get("/", response_model=List[ProjectItem], status_code=status.HTTP_200_OK)
def get_projects(user_id: Optional[str] = None, db: Session = Depends(get_db)):
    logger.info(f"Fetching projects list for user_id: {user_id}")
    # Mocking project list return
    return [
        ProjectItem(
            id="mock-project-id-1",
            name="My AI Design Builder Website",
            description="Testing landing pages generation",
            user_id=user_id or "default-user-id"
        )
    ]
