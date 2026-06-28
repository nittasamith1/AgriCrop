"""
test_integration.py – Integration tests for system health and basic endpoints
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_health_check():
    """Verify that the health check endpoint returns 200 and healthy status when DB is ok."""
    # We patch backend.main.db to simulate a healthy MongoDB connection
    with patch("backend.main.db") as mock_db:
        # Create a mock for client.admin.command
        mock_db.client = MagicMock()
        mock_db.client.admin = MagicMock()
        mock_db.client.admin.command = AsyncMock(return_value={"ok": 1})

        response = client.get("/api/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
        assert response.json()["database"] == "connected"

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
