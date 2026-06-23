import logging
from backend.knowledge.prefect_flow import DailyKnowledgeFlow

logger = logging.getLogger(__name__)


def deploy_scheduler():
    """Builds and returns the Prefect deployment for the daily knowledge ingestion flow

    with scheduled runs at 09:00 and 18:00.
    """
    logger.info("Initializing Prefect Ingestion flow scheduler...")
    try:
        from prefect.client.schemas.schedules import CronSchedule

        try:
            # Attempt to set multiple schedules (Prefect 2.x/3.x)
            deployment = DailyKnowledgeFlow.to_deployment(
                name="Daily Ingestion Scan",
                schedules=[
                    CronSchedule(cron="0 9 * * *", timezone="UTC"),
                    CronSchedule(cron="0 18 * * *", timezone="UTC"),
                ],
            )
        except Exception:
            # Fallback to single schedule
            deployment = DailyKnowledgeFlow.to_deployment(
                name="Daily Ingestion Scan",
                schedule=CronSchedule(cron="0 9 * * *", timezone="UTC"),
            )
        logger.info("Prefect deployment 'Daily Ingestion Scan' defined successfully.")
        return deployment
    except Exception as e:
        logger.error(f"Failed to define Prefect deployment schedule: {e}")
        return None


if __name__ == "__main__":
    deploy_scheduler()
