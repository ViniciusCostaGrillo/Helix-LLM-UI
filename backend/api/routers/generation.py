from fastapi import APIRouter, Depends, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.database.models import Execution, Job
from backend.database.session import get_db
from backend.utils.custom_logger import setup_logger
from backend.workers.queue import TaskQueue

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
    
    # 1. Initialize Execution
    execution = Execution(
        project_id=request.project_id,
        status="pending",
        config={"prompt": request.prompt}
    )
    db.add(execution)
    db.commit()
    db.refresh(execution)
    
    # 2. Initialize Job
    job = Job(
        name="prompt_generation",
        status="queued",
        execution_id=execution.id
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    
    # 3. Enqueue to high-priority task queue
    q = TaskQueue()
    q.enqueue(
        queue_name="generation_tasks",
        task_type="prompt_generation",
        payload={
            "execution_id": execution.id,
            "job_id": job.id,
            "project_id": request.project_id,
            "prompt": request.prompt
        },
        priority="high"
    )
    
    return GenerateResponse(
        execution_id=execution.id,
        status="pending"
    )

@router.post("/codegen", response_model=CodegenResponse, status_code=status.HTTP_202_ACCEPTED)
def start_codegen(request: CodegenRequest, db: Session = Depends(get_db)):
    logger.info(f"Received codegen request for execution {request.execution_id}")
    # Mocking codegen start
    return CodegenResponse(
        job_id="mock-job-id-codegen",
        status="processing"
    )


from backend.designer.visual_planning_engine import VisualPlanningEngine
from backend.schemas.designer import VisualPlan

class VisualPlanRequest(BaseModel):
    prompt: str

@router.post("/visual_plan", response_model=VisualPlan)
def get_visual_plan(request: VisualPlanRequest):
    logger.info(f"Received visual plan request for prompt: {request.prompt}")
    planner = VisualPlanningEngine()
    plan = planner.plan(request.prompt)
    return plan


