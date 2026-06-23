import os
import subprocess
import sys
import time

# List of test suites to execute
TEST_SCRIPTS = [
    "backend/utils/validate_env.py",
    "backend/utils/test_api.py",
    "backend/utils/test_crawlers.py",
    "backend/utils/test_extractor.py",
    "backend/utils/test_vision.py",
    "backend/utils/test_analyzer.py",
    "backend/utils/test_codegen.py",
    "backend/utils/test_dataset_builder.py",
    "backend/utils/test_embeddings.py",
    "backend/utils/test_chromadb.py",
    "backend/utils/test_agents.py",
    "backend/utils/test_pipeline.py",
    "backend/utils/test_workers.py",
    "backend/utils/test_prefect.py",
    "backend/utils/test_airflow.py",
    "backend/utils/test_rag.py",
    "backend/utils/test_training.py",
    "backend/utils/test_observability.py",
    "backend/utils/test_scalability.py",
    "backend/utils/test_complete_system.py",
    "backend/utils/test_motion_engine.py",
    "backend/utils/test_knowledge_engine.py",
    "backend/utils/test_upload_api.py",
]


def run_all():
    print("=" * 60)
    print("STARTING COMPLETE SYSTEM INTEGRATION VERIFICATION")
    print("=" * 60)

    # Use database URL for SQLite to avoid Docker container requirements during testing
    env = os.environ.copy()
    env["DATABASE_URL"] = "sqlite:///./test.db"
    env["ANALYTICS_DATABASE_URL"] = "sqlite:///./test_analytics.db"
    env["PYTHONPATH"] = "."

    python_executable = sys.executable

    results = []
    failed = False

    for script in TEST_SCRIPTS:
        script_name = os.path.basename(script)
        print(f"\n[RUNNING] {script_name}...")
        start_time = time.time()

        try:
            res = subprocess.run(
                [python_executable, script],
                env=env,
                capture_output=True,
                text=True,
                timeout=90,
            )
            duration = time.time() - start_time

            if res.returncode == 0:
                print(f"[PASS] {script_name} ({duration:.2f}s)")
                results.append((script_name, "PASS", duration, ""))
            else:
                print(f"[FAIL] {script_name} ({duration:.2f}s)")
                print("-" * 40)
                print(res.stderr or res.stdout)
                print("-" * 40)
                results.append((script_name, "FAIL", duration, res.stderr or res.stdout))
                failed = True
        except subprocess.TimeoutExpired:
            duration = time.time() - start_time
            print(f"[TIMEOUT] {script_name} ({duration:.2f}s)")
            results.append((script_name, "TIMEOUT", duration, "Execution exceeded timeout threshold."))
            failed = True
        except Exception as e:
            duration = time.time() - start_time
            print(f"[ERROR] {script_name} ({duration:.2f}s): {e}")
            results.append((script_name, "ERROR", duration, str(e)))
            failed = True

    print("\n" + "=" * 60)
    print("INTEGRATION VERIFICATION REPORT")
    print("=" * 60)
    print(f"{'Test Suite':<35} | {'Status':<8} | {'Duration':<8}")
    print("-" * 60)

    for name, status, duration, _ in results:
        status_label = "PASS" if status == "PASS" else status
        print(f"{name:<35} | {status_label:<8} | {duration:>6.2f}s")

    print("=" * 60)
    if failed:
        print("[RESULT] SOME TEST SUITES FAILED. PLEASE CHECK THE DETAILS ABOVE.")
        sys.exit(1)
    else:
        print("[RESULT] ALL TEST SUITES PASSED SUCCESSFULLY!")
        sys.exit(0)


if __name__ == "__main__":
    run_all()
