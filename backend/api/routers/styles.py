from fastapi import APIRouter, Depends, status
from typing import Any, Dict, List, Optional
from pydantic import BaseModel
from sqlalchemy.orm import Session
from backend.database.session import get_db
from backend.utils.custom_logger import setup_logger

logger = setup_logger("api.routers.styles")
router = APIRouter(prefix="/styles", tags=["styles"])

class StyleItem(BaseModel):
    id: str
    project_id: str
    colors: List[str]
    fonts: List[str]
    spacing_heuristics: Dict[str, Any]

@router.get("/", response_model=List[StyleItem], status_code=status.HTTP_200_OK)
def get_styles(project_id: Optional[str] = None, db: Session = Depends(get_db)):
    logger.info(f"Fetching styles for project_id: {project_id}")
    # Mocking styles return
    return [
        StyleItem(
            id="mock-style-id-1",
            project_id=project_id or "default-project-id",
            colors=["#09090b", "#3f3f46", "#ffffff"],
            fonts=["Inter", "Outfit"],
            spacing_heuristics={"padding": "dense", "container-max-width": "1280px"}
        )
    ]
