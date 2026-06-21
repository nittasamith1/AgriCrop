"""
AgriCrop – Pydantic Models: User
Defines request/response schemas for user registration, profile, and updates.
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field, field_validator


class UserRegisterRequest(BaseModel):
    """Payload for user registration."""
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    name: str = Field(..., min_length=2, max_length=100)
    role: str = Field(default="farmer", pattern="^(farmer|admin)$")
    phone: Optional[str] = Field(default=None, pattern=r"^\+?[\d\s\-]{7,15}$")
    state: Optional[str] = None
    district: Optional[str] = None


class UserLoginRequest(BaseModel):
    """Payload for login (used to generate a custom token for testing)."""
    email: EmailStr
    password: str


class UserProfileResponse(BaseModel):
    """Public user profile returned by the API."""
    uid: str
    email: str
    name: str
    role: str = "farmer"
    phone: Optional[str] = None
    state: Optional[str] = None
    district: Optional[str] = None
    profile_picture_url: Optional[str] = None
    farm_ids: List[str] = []
    is_email_verified: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    total_predictions: int = 0
    is_active: bool = True


class UserUpdateRequest(BaseModel):
    """Fields a user can update in their profile."""
    name: Optional[str] = Field(default=None, min_length=2, max_length=100)
    phone: Optional[str] = Field(default=None, pattern=r"^\+?[\d\s\-]{7,15}$")
    state: Optional[str] = None
    district: Optional[str] = None
    profile_picture_url: Optional[str] = None


class FarmCreateRequest(BaseModel):
    """Add a new farm location."""
    name: str = Field(..., min_length=2, max_length=100)
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    area_acres: Optional[float] = Field(default=None, ge=0)
    crop_types: Optional[List[str]] = []
    soil_type: Optional[str] = None
    district: Optional[str] = None
    state: Optional[str] = None


class FarmResponse(BaseModel):
    """Farm document returned by API."""
    farm_id: str
    user_id: str
    name: str
    latitude: float
    longitude: float
    area_acres: Optional[float] = None
    crop_types: List[str] = []
    soil_type: Optional[str] = None
    district: Optional[str] = None
    state: Optional[str] = None
    created_at: Optional[datetime] = None


class TokenResponse(BaseModel):
    """JWT token response."""
    access_token: str
    token_type: str = "bearer"
    uid: str
    email: str
    role: str
    name: str


class MessageResponse(BaseModel):
    """Generic message response."""
    message: str
    success: bool = True
