from fastapi.testclient import TestClient
from main import app

# Create a test client using our factory-instantiated app
client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_analyze_invalid_path():
    # Test that our API correctly rejects fake paths
    response = client.post("/api/analyze", json={"repo_path": "/fake/nonexistent/repo/path"})
    
    assert response.status_code == 400
    assert "does not exist" in response.json()["detail"]