import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_health_check():
    """Verify that the health check endpoint returns 200 and healthy status."""
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_root_endpoint():
    """Verify that the root endpoint returns welcome message."""
    response = client.get("/")
    assert response.status_code == 200
    assert "Welcome" in response.json()["message"]

def test_docs_exist():
    """Verify OpenAPI documentation exists."""
    response = client.get("/api/openapi.json")
    assert response.status_code == 200
    assert "openapi" in response.json()
