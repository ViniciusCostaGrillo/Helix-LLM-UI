import time
import logging
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

from backend.database.session import SessionLocal
from backend.workers.queue import TaskQueue

logger = logging.getLogger(__name__)


class BackgroundWorker:
    """Worker daemon listening to task queues and processing them in parallel."""
    
    def __init__(self, queue_name: str = "generation_tasks"):
        self.queue_name = queue_name
        self.queue = TaskQueue()
        self.executor = None
        self.running = False

    def start(self, concurrency: int = 4):
        logger.info(
            f"Starting BackgroundWorker for queue '{self.queue_name}' with concurrency={concurrency}..."
        )
        self.executor = ThreadPoolExecutor(max_workers=concurrency)
        self.running = True
        
        try:
            self.listen()
        except KeyboardInterrupt:
            logger.info("Worker daemon received shutdown signal via KeyboardInterrupt.")
            self.stop()

    def listen(self):
        while self.running:
            try:
                task = self.queue.dequeue(self.queue_name, timeout=1)
                if task:
                    logger.info(f"Worker dequeued task ID={task.get('task_id')}. Dispatching to executor...")
                    self.executor.submit(self.process_task, task)
            except Exception as e:
                logger.error(f"Error in worker main listener loop: {e}")
                time.sleep(1)

    def stop(self):
        logger.info("Stopping worker executor pool...")
        self.running = False
        if self.executor:
            self.executor.shutdown(wait=True)
        logger.info("Worker daemon stopped.")

    def process_task(self, task: dict):
        db = SessionLocal()
        execution_id = None
        job_id = None
        try:
            payload = task.get("payload", {})
            execution_id = payload.get("execution_id")
            job_id = payload.get("job_id")
            project_id = payload.get("project_id", "1")
            url = payload.get("url", "https://example.com")
            target_framework = payload.get("target_framework", "React")
            
            logger.info(
                f"Processing task ID={task.get('task_id')} | "
                f"execution={execution_id} | job={job_id} | project={project_id}"
            )

            from backend.database.models import Execution, Job, Log
            
            # Retrieve or create execution
            execution = None
            if execution_id:
                execution = db.query(Execution).filter(Execution.id == execution_id).first()
            
            if not execution:
                execution = Execution(
                    project_id=project_id,
                    status="running",
                    config=payload
                )
                db.add(execution)
                db.commit()
                db.refresh(execution)
                execution_id = execution.id
            else:
                execution.status = "running"
                db.commit()

            # Retrieve or create job
            job = None
            if job_id:
                job = db.query(Job).filter(Job.id == job_id).first()
            if not job:
                job = Job(
                    name="pipeline_run",
                    status="processing",
                    execution_id=execution_id
                )
                db.add(job)
                db.commit()
                db.refresh(job)
                job_id = job.id
            else:
                job.status = "processing"
                db.commit()

            # Log start event
            db.add(Log(
                execution_id=execution_id,
                job_id=job_id,
                level="INFO",
                message=f"Starting multi-agent execution pipeline for project {project_id} (url={url})."
            ))
            db.commit()

            # Run LangGraph pipeline
            from backend.agents.langgraph_agent import LangGraphAgent
            from backend.schemas.agents import AgentRunContext
            
            context = AgentRunContext(
                html_content=payload.get("html_content"),
                css_content=payload.get("css_content"),
                screenshot_path=payload.get("screenshot_path"),
                target_framework=target_framework,
                metadata={"url": url, "project_id": str(project_id)}
            )
            
            pipeline = LangGraphAgent()
            result = pipeline.run(context)
            
            # Write agent messages logs
            for msg in result.messages:
                db.add(Log(
                    execution_id=execution_id,
                    job_id=job_id,
                    level="INFO",
                    message=f"[{msg.sender}]: {msg.content}"
                ))
            
            if result.success:
                logger.info(f"Task ID={task.get('task_id')} completed successfully.")
                execution.status = "completed"
                execution.finished_at = datetime.utcnow()
                execution.result = result.output_data
                job.status = "success"
                
                db.add(Log(
                    execution_id=execution_id,
                    job_id=job_id,
                    level="INFO",
                    message="Multi-agent execution pipeline completed successfully."
                ))
            else:
                error_msg = result.metadata.get("error") or "Unknown error"
                logger.error(f"Task ID={task.get('task_id')} failed: {error_msg}")
                execution.status = "failed"
                execution.error_message = error_msg
                execution.finished_at = datetime.utcnow()
                job.status = "failed"
                
                db.add(Log(
                    execution_id=execution_id,
                    job_id=job_id,
                    level="ERROR",
                    message=f"Multi-agent execution pipeline failed: {error_msg}."
                ))
                
            db.commit()
        except Exception as e:
            logger.exception(f"Exception raised in worker task processor: {e}")
            db.rollback()
            try:
                from backend.database.models import Execution, Job, Log
                # Handle fallback tracking on DB failures
                if execution_id:
                    execution = db.query(Execution).filter(Execution.id == execution_id).first()
                    if execution:
                        execution.status = "failed"
                        execution.error_message = str(e)
                        execution.finished_at = datetime.utcnow()
                if job_id:
                    job = db.query(Job).filter(Job.id == job_id).first()
                    if job:
                        job.status = "failed"
                db.add(Log(
                    execution_id=execution_id,
                    job_id=job_id,
                    level="ERROR",
                    message=f"Worker processor encountered unhandled exception: {str(e)}."
                ))
                db.commit()
            except Exception as dbe:
                logger.exception(f"Failed to record traceback to DB: {dbe}")
        finally:
            db.close()


if __name__ == "__main__":
    import sys
    logging.basicConfig(
        level=logging.INFO,
        format="[%(asctime)s] %(levelname)s in %(name)s: %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)]
    )
    worker = BackgroundWorker()
    worker.start()
