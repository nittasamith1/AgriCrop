"""
AgriCrop – Pydantic Models: Prediction
Defines schemas for disease detection and soil moisture prediction
requests, responses, and history records.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


# ── Disease Detection ─────────────────────────────────────────────────────────

class DiseaseDetectionResponse(BaseModel):
    """Result returned after processing a leaf image."""
    prediction_id: str
    user_id: str
    farm_id: Optional[str] = None
    image_url: str
    disease_name: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    severity: str  # "healthy" | "mild" | "moderate" | "severe"
    affected_area_percent: float
    crop_type: Optional[str] = None
    treatments: List[str] = []
    prevention_tips: List[str] = []
    recommended_pesticides: List[str] = []
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    district: Optional[str] = None
    state: Optional[str] = None
    created_at: datetime
    model_version: str = "MobileNetV2-v1"


class DiseasePredictionHistory(BaseModel):
    """Compact record for history list view."""
    prediction_id: str
    disease_name: str
    confidence: float
    severity: str
    crop_type: Optional[str] = None
    image_url: str
    created_at: datetime
    farm_id: Optional[str] = None


# ── Soil Moisture Prediction ──────────────────────────────────────────────────

class SoilPredictionRequest(BaseModel):
    """Input features for soil moisture prediction model."""
    temperature: float = Field(..., ge=-10, le=60, description="Temperature in °C")
    humidity: float = Field(..., ge=0, le=100, description="Relative humidity %")
    rainfall: float = Field(..., ge=0, le=500, description="Rainfall in mm")
    wind_speed: float = Field(default=10.0, ge=0, le=150, description="Wind speed in km/h")
    soil_type: str = Field(default="loamy", description="sandy|loamy|clay|silt|peaty")
    previous_moisture: float = Field(default=50.0, ge=0, le=100, description="Previous moisture %")
    farm_id: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

    @classmethod
    def soil_type_to_index(cls, soil_type: str) -> int:
        mapping = {"sandy": 0, "loamy": 1, "clay": 2, "silt": 3, "peaty": 4}
        return mapping.get(soil_type.lower(), 1)


class SoilPredictionResponse(BaseModel):
    """Result returned after soil moisture prediction."""
    prediction_id: str
    user_id: str
    farm_id: Optional[str] = None
    predicted_moisture: float
    water_requirement_mm: float
    irrigation_recommended: bool
    irrigation_type: str  # "drip" | "sprinkler" | "flood" | "none"
    next_irrigation_hours: Optional[int] = None
    recommendation_text: str
    input_features: Dict[str, Any]
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    created_at: datetime
    model_version: str = "DenseNN-v1"


class SoilPredictionHistory(BaseModel):
    """Compact record for history list view."""
    prediction_id: str
    predicted_moisture: float
    irrigation_recommended: bool
    irrigation_type: str
    created_at: datetime
    farm_id: Optional[str] = None


# ── Combined History ──────────────────────────────────────────────────────────

class PredictionHistoryResponse(BaseModel):
    """Paginated combined prediction history."""
    total: int
    page: int
    page_size: int
    disease_predictions: List[DiseasePredictionHistory] = []
    soil_predictions: List[SoilPredictionHistory] = []


# ── Notification ──────────────────────────────────────────────────────────────

class NotificationModel(BaseModel):
    """Notification document."""
    notification_id: str
    user_id: str
    title: str
    message: str
    type: str  # "disease_alert" | "soil_alert" | "system" | "report_ready"
    is_read: bool = False
    related_id: Optional[str] = None  # prediction_id or report_id
    created_at: datetime


# ── Report ────────────────────────────────────────────────────────────────────

class ReportRequest(BaseModel):
    """Request to generate a PDF report."""
    report_type: str = Field(..., pattern="^(disease|soil|combined|admin)$")
    farm_id: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    include_charts: bool = True


class ReportResponse(BaseModel):
    """Report generation result."""
    report_id: str
    user_id: str
    report_type: str
    file_url: str
    file_name: str
    created_at: datetime
    expires_at: Optional[datetime] = None
