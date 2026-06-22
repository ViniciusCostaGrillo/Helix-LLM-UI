import sys
import time
import threading
from pathlib import Path

# Ensure backend can be imported correctly
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from backend.database.session import engine, SessionLocal, Base
from backend.database.models import User, Project, Execution, Job, Log
from backend.workers.queue import TaskQueue
from backend.workers.worker import BackgroundWorker
from backend.utils.custom_logger import setup_logger

logger = setup_logger("utils.test_workers")


def init_db_schema():
    logger.info("Verifying and creating database schemas...")
    Base.metadata.create_all(bind=engine)


def run_tests() -> None:
    logger.info("Initializing Workers Queue Test Harness...")
    init_db_schema()

    db = SessionLocal()
    try:
        # 1. Setup User and Project
        logger.info("Setting up database records...")
        user = db.query(User).first()
        if not user:
            user = User(email="test_worker@example.com", name="Worker Tester")
            db.add(user)
            db.commit()
            db.refresh(user)

        project = db.query(Project).filter(Project.user_id == user.id).first()
        if not project:
            project = Project(name="Worker Test Project", description="Test worker pipeline queue", user_id=user.id)
            db.add(project)
            db.commit()
            db.refresh(project)

        # 2. Setup Execution and Job
        execution = Execution(
            project_id=project.id,
            status="pending",
            config={"test": True}
        )
        db.add(execution)
        db.commit()
        db.refresh(execution)

        job = Job(
            name="pipeline_run",
            status="queued",
            execution_id=execution.id
        )
        db.add(job)
        db.commit()
        db.refresh(job)

        logger.info(f"Database records created. Execution ID={execution.id}, Job ID={job.id}")

        # 3. Setup Task Queue & Enqueue task
        queue_name = "test_tasks_queue"
        t_queue = TaskQueue()
        
        # Clean previous queue items if any
        while t_queue.length(queue_name) > 0:
            t_queue.dequeue(queue_name, timeout=1)
            
        payload = {
            "execution_id": execution.id,
            "job_id": job.id,
            "project_id": "3",  # creates site_000003
            "url": "https://example.com",
            "target_framework": "React"
        }
        
        task_id = t_queue.enqueue(queue_name, "pipeline_run", payload)
        assert t_queue.length(queue_name) == 1, "Failed to enqueue task!"
        logger.info(f"[PASS] Task enqueued with ID: {task_id}")

        # 4. Start BackgroundWorker in daemon thread
        logger.info("Launching BackgroundWorker thread...")
        worker = BackgroundWorker(queue_name=queue_name)
        
        # Run worker loop in background thread
        worker_thread = threading.Thread(
            target=worker.start,
            kwargs={"concurrency": 2},
            daemon=True
        )
        worker_thread.start()

        # Wait for worker to dequeue and process
        logger.info("Waiting for background task execution (up to 45 seconds)...")
        timeout_seconds = 45
        elapsed = 0
        success = False
        
        while elapsed < timeout_seconds:
            time.sleep(1)
            elapsed += 1
            # Refresh DB states
            db.refresh(execution)
            db.refresh(job)
            logger.info(f"Checking states... Execution status={execution.status}, Job status={job.status}")
            if execution.status in ("completed", "failed"):
                success = True
                break

        # Stop worker daemon
        logger.info("Stopping BackgroundWorker daemon...")
        worker.stop()

        # 5. Assertions
        logger.info("Running database assertions...")
        assert success is True, "Worker did not complete task execution within timeout!"
        assert execution.status == "completed", f"Execution status failed: {execution.error_message}"
        assert job.status == "success", f"Job status was not success: {job.status}"
        
        # Verify logs were written
        logs = db.query(Log).filter(Log.execution_id == execution.id).all()
        assert len(logs) > 0, "No log records written to DB!"
        
        logger.info(f"[PASS] Logs written to database: {len(logs)} records found.")
        for log in logs:
            logger.info(f"  [{log.level}] {log.message}")

        # 6. Verify Parallel executions validation
        logger.info("Testing parallel queue execution capability...")
        task_id_a = t_queue.enqueue(queue_name, "pipeline_run", {"project_id": "4", "url": "https://example.com/a"})
        task_id_b = t_queue.enqueue(queue_name, "pipeline_run", {"project_id": "5", "url": "https://example.com/b"})
        
        assert t_queue.length(queue_name) == 2, "Fail enqueuing tasks in parallel test"
        
        # Run single dequeue processes directly to verify queue emptying
        logger.info("Retrieving queued parallel tasks...")
        ta = t_queue.dequeue(queue_name, timeout=1)
        tb = t_queue.dequeue(queue_name, timeout=1)
        
        assert ta is not None and tb is not None, "Failed to dequeue parallel tasks"
        assert ta["task_id"] == task_id_a, "Task order mismatch"
        assert tb["task_id"] == task_id_b, "Task order mismatch"
        
        logger.info("[PASS] Parallel enqueues and dequeues successfully verified.")
        logger.info("ALL WORKER QUEUE CHECKS PASSED SUCCESSFULLY!")

    except Exception as e:
        logger.error(f"Workers queue test failed: {e}")
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    run_tests()
