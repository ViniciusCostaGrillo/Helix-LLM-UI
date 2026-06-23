import logging
from prefect import flow, task
from backend.knowledge.watchdog import KnowledgeWatchdog

logger = logging.getLogger(__name__)


@task(name="Scan Ingestion Folders")
def scan_ingestion_folders_task():
    logger.info("Prefect Task: scanning knowledge_input/ folders...")
    watchdog = KnowledgeWatchdog()
    # Trigger a single complete scan to process any new or modified files
    watchdog.scan_once()
    logger.info("Prefect Task: finished scanning knowledge_input/ folders.")
    return {"status": "success"}


@flow(name="DailyKnowledgeFlow")
def DailyKnowledgeFlow():
    """Daily Knowledge Flow that audits and ingests new UI assets, components,

    themes, and skills.
    """
    logger.info("Prefect Flow: Starting DailyKnowledgeFlow...")
    status = scan_ingestion_folders_task()
    logger.info("Prefect Flow: DailyKnowledgeFlow finished.")
    return status


if __name__ == "__main__":
    # Allow direct invocation for debugging or standalone execution
    DailyKnowledgeFlow()
