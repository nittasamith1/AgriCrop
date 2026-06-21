import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

from backend.main import app
from backend.dependencies import get_current_user

client = TestClient(app)

# Mocked current user dependency
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
    with patch("backend.routers.disease.storage_service") as mock_storage, \
         patch("backend.services.firebase_service.get_firestore_client") as mock_firestore, \
         patch("backend.routers.disease.notification_service") as mock_notif, \
         patch("backend.routers.disease.validate_image_upload") as mock_validate:
        
        mock_storage.upload_leaf_image.return_value = "https://mock-image-url.com/leaf.jpg"
        mock_validate.return_value = b"mock-image-bytes"
        
        # Mock Firestore Instance
        db_mock = MagicMock()
        mock_firestore.return_value = db_mock
        
        yield {
            "storage": mock_storage,
            "firestore": db_mock,
            "notif": mock_notif
        }

def test_predict_disease(mock_firebase_services):
    app.dependency_overrides[get_current_user] = override_get_current_user

    # Mock prediction output
    mock_prediction = {
        "disease_class_key": "Tomato___healthy",
        "disease_name": "Tomato – healthy",
        "confidence": 0.95,
        "severity": "healthy",
        "affected_area_percent": 0.0,
        "is_healthy": True,
        "top_predictions": [],
        "model_version": "MobileNetV2-v1",
        "stub_mode": True,
    }
    
    with patch("backend.routers.disease.disease_predictor.predict", return_value=mock_prediction):
        # Create a dummy file upload
        files = {"file": ("test.jpg", b"image-content", "image/jpeg")}
        response = client.post(
            "/api/v1/disease/predict",
            files=files,
            data={"notes": "Test prediction"}
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["disease_name"] == "Tomato – healthy"
        assert data["is_healthy"] is True
        assert data["image_url"] == "https://mock-image-url.com/leaf.jpg"

    app.dependency_overrides.clear()
