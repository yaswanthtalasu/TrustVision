import pytest
from fastapi.testclient import TestClient
from backend.api.main import app

client = TestClient(app)

def test_api_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert data["system"] == "TrustVision Data Integrity Assurance Engine"
