from fastapi import APIRouter, Depends, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from backend.database.session import get_db
from backend.utils.custom_logger import setup_logger

logger = setup_logger("api.routers.crawler")
router = APIRouter(prefix="/crawler", tags=["crawler"])

class CrawlRequest(BaseModel):
    project_id: str
    url: str

class CrawlResponse(BaseModel):
    job_id: str
    status: str

@router.post("/crawl", response_model=CrawlResponse, status_code=status.HTTP_202_ACCEPTED)
def start_crawl(request: CrawlRequest, db: Session = Depends(get_db)):
    logger.info(f"Received crawl request for url {request.url} in project {request.project_id}")
    # Mocking crawl start, real code will run Playwright / Crawl4AI task in background queue
    return CrawlResponse(
        job_id="mock-job-id-crawler",
        status="processing"
    )
