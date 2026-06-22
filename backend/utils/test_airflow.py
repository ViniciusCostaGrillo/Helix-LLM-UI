import sys
from pathlib import Path

# Ensure backend can be imported correctly
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from backend.orchestration.airflow_dag import dag
from backend.utils.custom_logger import setup_logger
from airflow import DAG

logger = setup_logger("utils.test_airflow")


def run_tests() -> None:
    logger.info("Initializing Airflow DAG Compilation Test Harness...")

    # 1. Assert DAG instance loaded
    logger.info("Verifying DAG instance load...")
    assert dag is not None, "Failed to load daily DAG!"
    assert isinstance(dag, DAG), "Loaded object is not an instance of airflow.DAG!"
    logger.info(f"[PASS] DAG loaded successfully: ID={dag.dag_id}")

    # 2. Assert basic configurations
    logger.info("Verifying DAG configurations...")
    assert dag.dag_id == "ui_ai_daily_generation_pipeline", "DAG ID mismatch!"
    assert dag.catchup is False, "DAG catchup must be disabled (False)!"
    assert "1 day" in str(dag.schedule) or "daily" in str(dag.schedule).lower(), "DAG schedule interval mismatch!"
    logger.info(f"[PASS] Basic configs checked: Schedule={dag.schedule}, Catchup={dag.catchup}")

    # 3. Assert tasks list and dependencies
    logger.info("Verifying tasks and task dependencies...")
    expected_tasks = [
        "crawl_page",
        "extract_content",
        "analyze_visuals",
        "resolve_styles",
        "generate_code",
        "package_dataset",
        "index_vectors"
    ]
    
    # Verify all tasks are defined
    task_dict = dag.task_dict
    for task_id in expected_tasks:
        assert task_id in task_dict, f"Expected task '{task_id}' not found in DAG task graph!"
    logger.info(f"[PASS] Found all {len(expected_tasks)} expected tasks in DAG graph.")

    # Verify sequential pipeline dependencies:
    # crawl_page >> extract_content >> analyze_visuals >> resolve_styles >> generate_code >> package_dataset >> index_vectors
    
    crawl = task_dict["crawl_page"]
    extract = task_dict["extract_content"]
    vision = task_dict["analyze_visuals"]
    style = task_dict["resolve_styles"]
    codegen = task_dict["generate_code"]
    dataset = task_dict["package_dataset"]
    rag = task_dict["index_vectors"]
    
    # Assert upstream/downstream relations
    assert extract.task_id in [t.task_id for t in crawl.downstream_list], "extract_content must be downstream of crawl_page!"
    assert vision.task_id in [t.task_id for t in extract.downstream_list], "analyze_visuals must be downstream of extract_content!"
    assert style.task_id in [t.task_id for t in vision.downstream_list], "resolve_styles must be downstream of analyze_visuals!"
    assert codegen.task_id in [t.task_id for t in style.downstream_list], "generate_code must be downstream of resolve_styles!"
    assert dataset.task_id in [t.task_id for t in codegen.downstream_list], "package_dataset must be downstream of generate_code!"
    assert rag.task_id in [t.task_id for t in dataset.downstream_list], "index_vectors must be downstream of package_dataset!"
    
    logger.info("[PASS] Task dependency execution graph checks passed.")
    logger.info("------------- Task Graph Hierarchy -------------")
    for t_id in expected_tasks:
        task_instance = task_dict[t_id]
        downstreams = [t.task_id for t in task_instance.downstream_list]
        logger.info(f"Task: '{t_id}' -> Downstream tasks: {downstreams}")

    logger.info("ALL AIRFLOW DAG CHECKS PASSED SUCCESSFULLY!")


if __name__ == "__main__":
    run_tests()
