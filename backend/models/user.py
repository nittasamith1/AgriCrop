"""
AgriCrop – User Models and Pydantic Schemas
Defines request/response models for authentication, profile, and farm management.
"""

from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime


# ── Request Models ────────────────────────────────────────────────────────────

class UserRegisterRequest(BaseModel):
    """User registration payload."""
    email: EmailStr
    password: str = Field(..., min_length=8, description="Password must be at least 8 characters")
    name: str = Field(..., min_length=2, max_length=100)
    role: str = Field(default="farmer", description="Role: farmer or admin")
    phone: Optional[str] = None
    state: Optional[str] = None
    district: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "email": "farmer@example.com",
                "password": "SecurePass123",
                "name": "John Farmer",
                "role": "farmer",
                "phone": "+91 9876543210",
                "state": "Karnataka",
                "district": "Bangalore",
            }
        }


class UserUpdateRequest(BaseModel):
    """Update user profile."""
    name: Optional[str] = None
    phone: Optional[str] = None
    state: Optional[str] = None
    district: Optional[str] = None
    profile_picture_url: Optional[str] = None


class LocationModel(BaseModel):
    """Geographic location coordinates."""
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)


class FarmCreateRequest(BaseModel):
    """Create a new farm."""
    name: str = Field(..., min_length=2, max_length=100)
    location: LocationModel
    area_acres: float = Field(..., gt=0, description="Farm area in acres")
    crop_types: List[str] = Field(default_factory=list, description="List of crops grown")
    soil_type: Optional[str] = None
    district: Optional[str] = None
    state: Optional[str] = None
    irrigation_type: Optional[str] = None
    notes: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "name": "North Field",
                "location": {"latitude": 12.9716, "longitude": 77.5946},
                "area_acres": 5.5,
                "crop_types": ["Rice", "Wheat"],
                "soil_type": "Loamy",
                "district": "Bangalore",
                "state": "Karnataka",
                "irrigation_type": "Drip",
                "notes": "Well-maintained farm",
            }
        }


# ── Response Models ───────────────────────────────────────────────────────────

class UserProfileResponse(BaseModel):
    """User profile response."""
    uid: str
    email: str
    name: str
    role: str
    phone: Optional[str] = None
    state: Optional[str] = None
    district: Optional[str] = None
    profile_picture_url: Optional[str] = None
    farm_ids: List[str] = []
    is_email_verified: bool = False
    is_active: bool = True
    total_predictions: int = 0
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "uid": "user123",
                "email": "farmer@example.com",
                "name": "John Farmer",
                "role": "farmer",
                "phone": "+91 9876543210",
                "state": "Karnataka",
                "district": "Bangalore",
                "profile_picture_url": None,
                "farm_ids": ["farm001", "farm002"],
                "is_email_verified": True,
                "is_active": True,
                "total_predictions": 42,
                "created_at": "2025-06-26T10:30:00Z",
                "updated_at": "2025-06-26T15:45:00Z",
            }
        }


class FarmResponse(BaseModel):
    """Farm details response."""
    farm_id: str
    user_id: str
    name: str
    latitude: float
    longitude: float
    area_acres: float
    crop_types: List[str]
    soil_type: Optional[str] = None
    district: Optional[str] = None
    state: Optional[str] = None
    irrigation_type: Optional[str] = None
    notes: Optional[str] = None
    total_predictions: int = 0
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "farm_id": "farm001",
                "user_id": "user123",
                "name": "North Field",
                "latitude": 12.9716,
                "longitude": 77.5946,
                "area_acres": 5.5,
                "crop_types": ["Rice", "Wheat"],
                "soil_type": "Loamy",
                "district": "Bangalore",
                "state": "Karnataka",
                "irrigation_type": "Drip",
                "notes": "Well-maintained farm",
                "total_predictions": 15,
                "created_at": "2025-06-26T10:30:00Z",
                "updated_at": "2025-06-26T15:45:00Z",
            }
        }


class MessageResponse(BaseModel):
    """Generic message response."""
    message: str

    class Config:
        json_schema_extra = {
            "example": {
                "message": "Operation completed successfully."
            }
        }


class DiseaseResultResponse(BaseModel):
    """Disease prediction result."""
    success: bool
    prediction_id: str
    disease_name: str
    confidence: float
    confidence_percent: str
    severity: str
    affected_area_percent: float
    is_healthy: bool
    crop_type: Optional[str] = None
    image_url: str
    treatments: List[str]
    prevention_tips: List[str]
    recommended_pesticides: List[str]
    organic_alternatives: List[str]
    top_predictions: List[dict]
    image_quality: dict
    stub_mode: bool
    model_version: str
    created_at: str


class SoilResultResponse(BaseModel):
    """Soil moisture prediction result."""
    success: bool
    prediction_id: str
    predicted_moisture: float
    moisture_percent: str
    irrigation_recommendation: str
    next_watering_days: int
    confidence: float
    created_at: str
