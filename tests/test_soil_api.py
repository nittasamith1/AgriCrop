"""
test_soil_api.py – Soil moisture prediction tests (MongoDB mocks, no Firebase)
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient

from backend.main import app
from backend.dependencies import get_current_user

client = TestClient(app)

# ── Shared user override ───────────────────────────────────────────────────────

async def override_get_current_user():
    return {
        "uid": "test-user-123",
        "email": "farmer@example.com",
        "name": "Samith Nitta",
        "role": "farmer",
        "total_predictions": 0,
        "is_active": True,
    }


# ── Mock AI prediction result ──────────────────────────────────────────────────

MOCK_SOIL_PREDICTION = {
    "predicted_moisture": 32.5,
    "field_capacity": 38.0,
    "wilting_point": 12.0,
    "available_water_content": 26.0,
    "water_requirement_mm": 5.4,
    "irrigation_recommended": True,
    "irrigation_type": "drip",
    "next_irrigation_hours": 12,
    "soil_type": "loamy",
    "input_features": {},
    "stub_mode": True,
    "model_version": "dense-v1",
}

VALID_SOIL_PAYLOAD = {
    "temperature": 24.5,
    "humidity": 60.0,
    "rainfall": 10.5,
    "wind_speed": 3.5,
    "soil_type": "loamy",
    "previous_moisture": 30.0,
    "farm_id": None,
    "latitude": 13.5,
    "longitude": 79.2,
}


# ── Test: POST /api/v1/soil/predict ──────────────────────────────────────────

def test_predict_soil_success():
    """Happy-path soil moisture prediction with mocked predictor and MongoDB writes."""
    app.dependency_overrides[get_current_user] = override_get_current_user

    with patch("backend.routers.soil.soil_predictor") as mock_predictor, \
         patch("backend.routers.soil._soil_svc") as mock_soil_svc, \
         patch("backend.routers.soil._user_svc") as mock_user_svc, \
         patch("backend.routers.soil._farm_svc") as mock_farm_svc, \
         patch("backend.routers.soil.notification_service") as mock_notif:

        mock_predictor.predict.return_value = MOCK_SOIL_PREDICTION
        mock_soil_svc.create = AsyncMock(return_value=True)
        mock_user_svc.update = AsyncMock(return_value=True)

        # soil_alert is awaited inside the router — must be AsyncMock
        mock_notif.soil_alert = AsyncMock(return_value=None)

        response = client.post("/api/v1/soil/predict", json=VALID_SOIL_PAYLOAD)

        assert response.status_code == 201, response.text
        data = response.json()
        assert data["success"] is True
        assert data["predicted_moisture"] == 32.5
        assert data["irrigation_recommended"] is True

    app.dependency_overrides.clear()


def test_predict_soil_invalid_soil_type():
    """Passing an unsupported soil_type should return 400."""
    app.dependency_overrides[get_current_user] = override_get_current_user

    bad_payload = {**VALID_SOIL_PAYLOAD, "soil_type": "gravel"}
    response = client.post("/api/v1/soil/predict", json=bad_payload)
    assert response.status_code == 400

    app.dependency_overrides.clear()


def test_predict_soil_unauthorized():
    """Calling predict without auth should return 401."""
    response = client.post("/api/v1/soil/predict", json=VALID_SOIL_PAYLOAD)
    assert response.status_code == 401
