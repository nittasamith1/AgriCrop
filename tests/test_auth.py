import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)

@pytest.fixture
def mock_firebase_auth():
    with patch("backend.routers.auth.firebase_auth") as mock_auth:
        from firebase_admin import auth as fb_auth
        mock_auth.EmailAlreadyExistsError = fb_auth.EmailAlreadyExistsError
        yield mock_auth

@pytest.fixture
def mock_firestore():
    with patch("backend.services.firebase_service.get_firestore_client") as mock_client:
        mock_db = MagicMock()
        mock_client.return_value = mock_db
        yield mock_db

def test_register_success(mock_firebase_auth, mock_firestore):
    # Mock Firebase Auth user creation
    mock_user = MagicMock()
    mock_user.uid = "test-uid-123"
    mock_firebase_auth.create_user.return_value = mock_user
    mock_firebase_auth.generate_email_verification_link.return_value = "http://verify-link"

    # Mock Firestore User document write
    mock_doc = MagicMock()
    mock_firestore.collection.return_value.document.return_value = mock_doc

    payload = {
        "email": "farmer@example.com",
        "password": "strongpassword123",
        "name": "Samith Nitta",
        "role": "farmer",
        "phone": "+919876543210",
        "state": "Andhra Pradesh",
        "district": "Chittoor"
    }

    # Execute
    response = client.post("/api/v1/auth/register", json=payload)

    # Assertions
    assert response.status_code == 201
    assert "message" in response.json()
    assert mock_firebase_auth.create_user.called
    assert mock_firestore.collection.called

def test_forgot_password(mock_firebase_auth):
    mock_firebase_auth.generate_password_reset_link.return_value = "http://reset-link"

    response = client.post("/api/v1/auth/forgot-password?email=farmer@example.com")
    assert response.status_code == 200
    assert "Password reset link generated" in response.json()["message"]

def test_get_profile_unauthorized():
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401
