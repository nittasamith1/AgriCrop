import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

from backend.main import app
from backend.dependencies import get_current_user

client = TestClient(app)

async def override_get_current_user():
    return {
        "uid": "test-user-123",
        "email": "farmer@example.com",
        "name": "Samith Nitta",
        "role": "farmer",
        "total_predictions": 0,
    }

@pytest.fixture
def mock_firebase_services():
    with patch("backend.services.firebase_service.get_firestore_client") as mock_firestore, \
         patch("backend.routers.soil.notification_service") as mock_notif:
        
        db_mock = MagicMock()
        mock_firestore.return_value = db_mock
        yield {
            "firestore": db_mock,
            "notif": mock_notif
        }

def test_predict_soil(mock_firebase_services):
    app.dependency_overrides[get_current_user] = override_get_current_user

    # Mock prediction output
    mock_prediction = {
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
    
    with patch("backend.routers.soil.soil_predictor.predict", return_value=mock_prediction):
        payload = {
            "temperature": 24.5,
            "humidity": 60.0,
            "rainfall": 10.5,
            "wind_speed": 3.5,
            "soil_type": "loamy",
            "previous_moisture": 30.0,
            "farm_id": None,
            "latitude": 13.5,
            "longitude": 79.2
        }
        
        response = client.post("/api/v1/soil/predict", json=payload)
        
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["predicted_moisture"] == 32.5
        assert data["irrigation_recommended"] is True

    app.dependency_overrides.clear()
