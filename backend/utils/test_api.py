import sys
from fastapi.testclient import TestClient
from backend.api.main import app

client = TestClient(app)

def test_endpoints():
    print("Running API routing and validation checks...")
    success = True
    
    # 1. Health check
    try:
        r = client.get("/health")
        assert r.status_code == 200
        assert r.json()["status"] == "healthy"
        print("PASS - GET /health")
    except Exception as e:
        print(f"FAIL - GET /health ({e})")
        success = False

    # 2. Generation generate
    try:
        r = client.post("/generation/generate", json={"project_id": "test-project", "prompt": "build page"})
        assert r.status_code == 202
        assert "execution_id" in r.json()
        print("PASS - POST /generation/generate")
    except Exception as e:
        print(f"FAIL - POST /generation/generate ({e})")
        success = False

    # 3. Generation codegen
    try:
        r = client.post("/generation/codegen", json={"execution_id": "test-exec"})
        assert r.status_code == 202
        assert "job_id" in r.json()
        print("PASS - POST /generation/codegen")
    except Exception as e:
        print(f"FAIL - POST /generation/codegen ({e})")
        success = False

    # 4. Crawler crawl
    try:
        r = client.post("/crawler/crawl", json={"project_id": "test-project", "url": "http://example.com"})
        assert r.status_code == 202
        assert "job_id" in r.json()
        print("PASS - POST /crawler/crawl")
    except Exception as e:
        print(f"FAIL - POST /crawler/crawl ({e})")
        success = False

    # 5. Analyzer analyze
    try:
        r = client.post("/analyzer/analyze", json={"dataset_id": "test-dataset", "execution_id": "test-exec"})
        assert r.status_code == 202
        assert "job_id" in r.json()
        print("PASS - POST /analyzer/analyze")
    except Exception as e:
        print(f"FAIL - POST /analyzer/analyze ({e})")
        success = False

    # 6. Dataset register
    try:
        r = client.post("/dataset/dataset", json={"project_id": "test-project", "url": "http://example.com"})
        assert r.status_code == 201
        assert "dataset_id" in r.json()
        print("PASS - POST /dataset/dataset")
    except Exception as e:
        print(f"FAIL - POST /dataset/dataset ({e})")
        success = False

    # 7. Projects list
    try:
        r = client.get("/projects/", params={"user_id": "test-user"})
        assert r.status_code == 200
        assert len(r.json()) > 0
        print("PASS - GET /projects/")
    except Exception as e:
        print(f"FAIL - GET /projects/ ({e})")
        success = False

    # 8. Components list
    try:
        r = client.get("/components/", params={"project_id": "test-project"})
        assert r.status_code == 200
        assert len(r.json()) > 0
        print("PASS - GET /components/")
    except Exception as e:
        print(f"FAIL - GET /components/ ({e})")
        success = False

    # 9. Styles list
    try:
        r = client.get("/styles/", params={"project_id": "test-project"})
        assert r.status_code == 200
        assert len(r.json()) > 0
        print("PASS - GET /styles/")
    except Exception as e:
        print(f"FAIL - GET /styles/ ({e})")
        success = False

    if success:
        print("\nAll 9 routing and validation checks passed successfully!")
        sys.exit(0)
    else:
        print("\nSome API checks failed.")
        sys.exit(1)

if __name__ == "__main__":
    test_endpoints()
