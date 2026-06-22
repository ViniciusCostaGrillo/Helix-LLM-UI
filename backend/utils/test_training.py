import os
import shutil
import sys
import time
from pathlib import Path

# Ensure backend can be imported correctly
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from fastapi.testclient import TestClient
from backend.api.main import app
from backend.database.session import engine, Base
from backend.training.service import TrainingOrchestrationService
from backend.utils.custom_logger import setup_logger

logger = setup_logger("utils.test_training")


def run_tests() -> None:
    logger.info("Initializing FASE 22 model fine-tuning training validation test...")

    # Initialize relational database schemas if SQLite test DB is fresh
    Base.metadata.create_all(bind=engine)

    base_dir = Path(__file__).resolve().parent.parent.parent
    test_dataset_dir = base_dir / "dataset" / "site_training_mock_99"
    test_components_dir = test_dataset_dir / "components"
    test_dataset_output_json = base_dir / "storage" / "training" / "dataset_sft_test.json"

    # Reset any old directories
    if test_dataset_dir.exists():
        shutil.rmtree(test_dataset_dir)
    if test_dataset_output_json.exists():
        os.remove(test_dataset_output_json)

    # 1. Seed layout packages context
    logger.info("Seeding mock layout dataset packages for compiler test...")
    os.makedirs(test_components_dir, exist_ok=True)

    mock_manifest = {
        "site_id": 99,
        "url": "https://test-training-pipeline.com",
        "primary_color": "#ff007f",
        "background_color": "#111111",
        "components_count": 1
    }
    with open(test_dataset_dir / "manifest.json", "w", encoding="utf-8") as f:
        import json
        json.dump(mock_manifest, f, indent=2)

    mock_comp_code = (
        "import React from 'react';\n"
        "export default function PinkHero() {\n"
        "  return <section className=\"bg-[#111111] text-[#ff007f]\">Pink Custom Hero</section>;\n"
        "}"
    )
    with open(test_components_dir / "PinkHero.tsx", "w", encoding="utf-8") as f:
        f.write(mock_comp_code)

    # 2. Test SFT Dataset Compilation
    logger.info("Running SFT dataset compilation service...")
    service = TrainingOrchestrationService()
    samples_count = service.compile_dataset(
        base_dataset_dir=str(base_dir / "dataset"),
        output_json_path=str(test_dataset_output_json)
    )

    assert samples_count > 0, "No SFT training samples compiled!"
    assert test_dataset_output_json.exists(), "Dataset output JSON file not created!"

    with open(test_dataset_output_json, "r", encoding="utf-8") as f:
        compiled_data = json.load(f)
    assert len(compiled_data) == samples_count
    assert "instruction" in compiled_data[0]
    assert "input" in compiled_data[0]
    assert "output" in compiled_data[0]
    logger.info(f"[PASS] Dataset compilation checked: {samples_count} chat samples parsed.")

    # 3. Test API routers and background loop updates
    logger.info("Testing FastAPI training router endpoints via TestClient...")
    client = TestClient(app)

    payload = {
        "model_name": "llama-3-8b-ui-sft-test",
        "base_model": "unsloth/llama-3-8b-Instruct-bnb-4bit",
        "dataset_path": str(test_dataset_output_json),
        "epochs": 2
    }

    # A. POST /training/start
    post_res = client.post("/training/start", json=payload)
    assert post_res.status_code == 201, f"Training trigger failed: {post_res.text}"
    job_data = post_res.json()
    assert "id" in job_data
    assert job_data["status"] in ("pending", "running", "completed")
    job_id = job_data["id"]
    logger.info(f"[PASS] POST /training/start successful. JobID: {job_id}")

    # B. Poll status /training/status/{job_id} until completed (mock loop will finish within ~1-2 seconds)
    logger.info("Polling training status endpoint...")
    max_retries = 10
    completed = False
    
    for retry in range(max_retries):
        time.sleep(0.4)
        status_res = client.get(f"/training/status/{job_id}")
        assert status_res.status_code == 200
        status_data = status_res.json()
        
        logger.info(f"Poll {retry+1}: Status='{status_data['status']}', Loss={status_data['loss']}")
        if status_data["status"] == "completed":
            completed = True
            assert status_data["loss"] is not None and status_data["loss"] < 2.45
            break
        elif status_data["status"] == "failed":
            raise ValueError("Training background job transitioned to FAILED status!")

    assert completed is True, "Training job did not complete within the maximum timeout!"
    logger.info("[PASS] Fine-tuning background execution loop status transitions checked.")

    # C. Verify adapter files outputs
    adapter_config_path = base_dir / "models" / "adapters" / payload["model_name"] / "adapter_config.json"
    assert adapter_config_path.exists(), "Peft adapter configuration weights not saved!"
    with open(adapter_config_path, "r", encoding="utf-8") as f:
        peft_cfg = json.load(f)
    assert peft_cfg["peft_type"] == "LORA"
    assert peft_cfg["base_model_name_or_path"] == payload["base_model"]
    logger.info("[PASS] LoRA PEFT adapter weights check passed.")

    # D. GET /training/history
    history_res = client.get("/training/history")
    assert history_res.status_code == 200
    history_data = history_res.json()
    assert len(history_data) > 0
    assert any(h["id"] == job_id for h in history_data)
    logger.info("[PASS] GET /training/history history logs lookup checked.")

    # Clean up test directories
    shutil.rmtree(test_dataset_dir)
    os.remove(test_dataset_output_json)

    logger.info("ALL FASE 22 MODEL TRAINING INTEGRATION CHECKS PASSED SUCCESSFULLY!")


if __name__ == "__main__":
    run_tests()
