from fastapi import APIRouter, Depends, status
from typing import List, Optional
from pydantic import BaseModel
from sqlalchemy.orm import Session
from backend.database.session import get_db
from backend.utils.custom_logger import setup_logger

logger = setup_logger("api.routers.components")
router = APIRouter(prefix="/components", tags=["components"])

class ComponentItem(BaseModel):
    id: str
    project_id: str
    name: str
    code_path: str
    type: str  # button, card, navbar, landing

@router.get("/", response_model=List[ComponentItem], status_code=status.HTTP_200_OK)
def get_components(project_id: Optional[str] = None, db: Session = Depends(get_db)):
    logger.info(f"Fetching components list for project_id: {project_id}")
    # Mocking components list return
    return [
        ComponentItem(
            id="mock-component-id-1",
            project_id=project_id or "default-project-id",
            name="HeroSection",
            code_path="storage/components/HeroSection.tsx",
            type="landing"
        ),
        ComponentItem(
            id="mock-component-id-2",
            project_id=project_id or "default-project-id",
            name="PrimaryButton",
            code_path="storage/components/PrimaryButton.tsx",
            type="button"
        )
    ]
