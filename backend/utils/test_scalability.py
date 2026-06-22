import asyncio
import sys
import time
from pathlib import Path

# Ensure backend can be imported correctly
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from backend.database.cache import CacheManager, cache_response
from backend.database.models import Log, User
from backend.database.session import Base, SessionLocal
from backend.database.sharding import analytics_engine, core_engine
from backend.utils.custom_logger import setup_logger
from backend.workers.queue import TaskQueue

logger = setup_logger("utils.test_scalability")

# Ensure SQLite test tables are created locally in both core and analytics DBs
Base.metadata.drop_all(bind=core_engine)
Base.metadata.drop_all(bind=analytics_engine)
Base.metadata.create_all(bind=core_engine)
Base.metadata.create_all(bind=analytics_engine)



def test_database_sharding() -> None:
    logger.info("Testing vertical database sharding routing...")

    # 1. Insert records via the routing SessionLocal
    db = SessionLocal()
    try:
        user = User(email="scaling-test@example.com", name="Scaling User")
        db.add(user)
        db.commit()
        db.refresh(user)

        # Write log record (should route to analytics DB bind)
        log = Log(message="Log sharded message 123", level="INFO")
        db.add(log)
        db.commit()
    finally:
        db.close()

    # 2. Connect directly to engines to verify sharding location
    from sqlalchemy.orm import sessionmaker

    core_session = sessionmaker(bind=core_engine)()
    analytics_session = sessionmaker(bind=analytics_engine)()

    try:
        # User check (should exist in core, not analytics)
        user_in_core = (
            core_session.query(User)
            .filter(User.email == "scaling-test@example.com")
            .first()
        )
        user_in_analytics = (
            analytics_session.query(User)
            .filter(User.email == "scaling-test@example.com")
            .first()
        )

        assert user_in_core is not None, "User not found in Core DB!"
        assert (
            user_in_analytics is None
        ), "User should NOT be found in Analytics DB!"
        logger.info("[PASS] Transactional model mapped exclusively to Core DB bind.")

        # Log check (should exist in analytics, not core)
        log_in_core = (
            core_session.query(Log)
            .filter(Log.message == "Log sharded message 123")
            .first()
        )
        log_in_analytics = (
            analytics_session.query(Log)
            .filter(Log.message == "Log sharded message 123")
            .first()
        )

        assert log_in_core is None, "Log should NOT be found in Core DB!"
        assert (
            log_in_analytics is not None
        ), "Log not found in Analytics DB!"
        logger.info(
            "[PASS] Analytics log model mapped exclusively to Analytics DB bind."
        )
    finally:
        core_session.close()
        analytics_session.close()


def test_caching_system() -> None:
    logger.info("Testing CacheManager and cache_response decorator...")

    cache_mgr = CacheManager()
    cache_mgr.clear()

    # 1. Direct set / get verification
    cache_mgr.set("test_key", {"data": "cached_value"}, expire_seconds=1)
    assert cache_mgr.get("test_key") == {"data": "cached_value"}

    # Wait for expiration
    time.sleep(1.2)
    assert cache_mgr.get("test_key") is None
    logger.info("[PASS] Direct cache set, get, and expiration verified.")

    # 2. Sync decorator caching check
    sync_calls = 0

    @cache_response(expire_seconds=5)
    def my_sync_func(x: str) -> str:
        nonlocal sync_calls
        sync_calls += 1
        return f"sync_{x}"

    res1 = my_sync_func("test")
    res2 = my_sync_func("test")
    assert res1 == "sync_test"
    assert res2 == "sync_test"
    assert sync_calls == 1
    logger.info("[PASS] Sync cache_response decorator successfully cached result.")

    # 3. Async decorator caching check
    async_calls = 0

    @cache_response(expire_seconds=5)
    async def my_async_func(x: str) -> str:
        nonlocal async_calls
        async_calls += 1
        return f"async_{x}"

    res_a1 = asyncio.run(my_async_func("test"))
    res_a2 = asyncio.run(my_async_func("test"))
    assert res_a1 == "async_test"
    assert res_a2 == "async_test"
    assert async_calls == 1
    logger.info("[PASS] Async cache_response decorator successfully cached result.")


def test_priority_workers() -> None:
    logger.info("Testing task priority queuing and dequeuing...")

    t_queue = TaskQueue()
    queue_name = "test_priority_queue"

    # Clear existing list items in mock client
    client = t_queue.client
    for suffix in ["_high", "_default", "_low"]:
        client.delete(f"{queue_name}{suffix}")

    # Enqueue tasks in non-sequential order
    t_queue.enqueue(
        queue_name, "test_task", {"project_id": "low_task"}, priority="low"
    )
    t_queue.enqueue(
        queue_name, "test_task", {"project_id": "high_task"}, priority="high"
    )
    t_queue.enqueue(
        queue_name,
        "test_task",
        {"project_id": "default_task"},
        priority="default",
    )

    # Dequeue tasks using priority ordered list
    listen_list = [f"{queue_name}_high", f"{queue_name}_default", f"{queue_name}_low"]

    task_1 = t_queue.dequeue(listen_list, timeout=1)
    task_2 = t_queue.dequeue(listen_list, timeout=1)
    task_3 = t_queue.dequeue(listen_list, timeout=1)

    assert task_1 is not None
    assert task_2 is not None
    assert task_3 is not None

    assert task_1["payload"]["project_id"] == "high_task"
    assert task_2["payload"]["project_id"] == "default_task"
    assert task_3["payload"]["project_id"] == "low_task"

    logger.info(
        "[PASS] Tasks dequeued in correct priority order (High -> Default -> Low)."
    )


def main() -> None:
    logger.info("------------- Scalability Orchestration Tests -------------")
    try:
        test_database_sharding()
        test_caching_system()
        test_priority_workers()
        logger.info("ALL SCALABILITY VERIFICATION CHECKS PASSED SUCCESSFULLY!")
    except Exception as e:
        logger.error(f"Scalability verification check failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
