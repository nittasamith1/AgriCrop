"""
AgriCrop – Disease Detection Router
POST /api/v1/disease/predict   – Upload leaf image and detect disease
GET  /api/v1/disease/history   – Get disease prediction history for current user
GET  /api/v1/disease/{id}      – Get single prediction by ID
"""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile, status
from loguru import logger
from slowapi import Limiter
from slowapi.util import get_remote_address

from backend.config import settings
from backend.dependencies import get_current_user
from backend.ai.disease_predictor import disease_predictor
from backend.ai.recommendation_engine import get_disease_recommendations, get_crop_from_class
from backend.services.firebase_service import FirestoreService
from backend.services.storage_service import storage_service
from backend.services.notification_service import notification_service
from backend.utils.helpers import generate_id, utc_now, severity_from_confidence, marker_color_from_severity
from backend.utils.validators import validate_image_upload

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)

_disease_svc = FirestoreService(settings.COLLECTION_DISEASE_PREDICTIONS)
_pred_svc = FirestoreService(settings.COLLECTION_PREDICTIONS)
_user_svc = FirestoreService(settings.COLLECTION_USERS)
_farm_svc = FirestoreService(settings.COLLECTION_FARMS)


@router.post("/predict", status_code=status.HTTP_201_CREATED)
@limiter.limit("30/minute")
async def predict_disease(
    request: Request,
    file: UploadFile = File(..., description="Crop leaf image (JPG, PNG, WEBP)"),
    farm_id: Optional[str] = Form(default=None),
    crop_type: Optional[str] = Form(default=None),
    latitude: Optional[float] = Form(default=None),
    longitude: Optional[float] = Form(default=None),
    notes: Optional[str] = Form(default=None),
    current_user: dict = Depends(get_current_user),
):
    """
    Upload a crop leaf image and run disease detection using MobileNetV2.
    Returns disease name, confidence, severity, treatments, and prevention tips.
    """
    uid = current_user["uid"]

    # ── Validate image ────────────────────────────────────────────────────────
    image_bytes = await validate_image_upload(file)

    # ── Upload to Firebase Storage ────────────────────────────────────────────
    try:
        image_url = storage_service.upload_leaf_image(
            content=image_bytes,
            filename=file.filename or "leaf.jpg",
            user_id=uid,
            content_type=file.content_type or "image/jpeg",
        )
    except Exception as e:
        logger.error(f"Image upload failed: {e}")
        raise HTTPException(status_code=500, detail="Image upload failed. Please try again.")

    # ── Run AI Prediction ─────────────────────────────────────────────────────
    try:
        result = disease_predictor.predict(image_bytes=image_bytes, crop_hint=crop_type)
    except Exception as e:
        logger.error(f"Disease prediction failed: {e}")
        raise HTTPException(status_code=500, detail="Prediction failed. Please try again.")

    # ── Get Recommendations ───────────────────────────────────────────────────
    recommendations = get_disease_recommendations(
        disease_class_key=result["disease_class_key"],
        is_healthy=result["is_healthy"],
    )

    # ── Infer crop from class if not provided ─────────────────────────────────
    detected_crop = crop_type or get_crop_from_class(result["disease_class_key"])

    # ── Get farm location if farm_id provided ─────────────────────────────────
    farm_lat, farm_lon, district, state = latitude, longitude, None, None
    if farm_id:
        farm_doc = _farm_svc.get(farm_id)
        if farm_doc and farm_doc.get("user_id") == uid:
            farm_lat = farm_lat or farm_doc.get("latitude")
            farm_lon = farm_lon or farm_doc.get("longitude")
            district = farm_doc.get("district")
            state = farm_doc.get("state")

    # ── Build Prediction Record ───────────────────────────────────────────────
    prediction_id = generate_id("dpred")
    now = utc_now()
    severity = result["severity"]
    confidence = result["confidence"]

    prediction_doc = {
        "prediction_id": prediction_id,
        "user_id": uid,
        "farm_id": farm_id,
        "image_url": image_url,
        "disease_name": result["disease_name"],
        "disease_class_key": result["disease_class_key"],
        "confidence": confidence,
        "severity": severity,
        "affected_area_percent": result["affected_area_percent"],
        "crop_type": detected_crop,
        "is_healthy": result["is_healthy"],
        "treatments": recommendations["treatments"],
        "prevention_tips": recommendations["prevention"],
        "recommended_pesticides": recommendations["pesticides"],
        "organic_alternatives": recommendations.get("organic", []),
        "top_predictions": result["top_predictions"],
        "latitude": farm_lat,
        "longitude": farm_lon,
        "district": district,
        "state": state,
        "notes": notes,
        "marker_color": marker_color_from_severity(severity),
        "stub_mode": result.get("stub_mode", True),
        "model_version": result["model_version"],
        "created_at": now,
    }

    _disease_svc.create(prediction_id, prediction_doc)

    # Increment user total_predictions counter
    total = current_user.get("total_predictions", 0) + 1
    _user_svc.update(uid, {"total_predictions": total, "updated_at": now})

    # ── Send Notification ─────────────────────────────────────────────────────
    if not result["is_healthy"]:
        notification_service.disease_alert(
            user_id=uid,
            disease_name=result["disease_name"],
            severity=severity,
            prediction_id=prediction_id,
        )

    logger.info(
        f"Disease prediction: uid={uid} | {result['disease_name']} "
        f"({confidence:.1%}) | severity={severity} | pred_id={prediction_id}"
    )

    return {
        "success": True,
        "prediction_id": prediction_id,
        "disease_name": result["disease_name"],
        "confidence": confidence,
        "confidence_percent": f"{confidence * 100:.1f}%",
        "severity": severity,
        "affected_area_percent": result["affected_area_percent"],
        "is_healthy": result["is_healthy"],
        "crop_type": detected_crop,
        "image_url": image_url,
        "treatments": recommendations["treatments"],
        "prevention_tips": recommendations["prevention"],
        "recommended_pesticides": recommendations["pesticides"],
        "organic_alternatives": recommendations.get("organic", []),
        "top_predictions": result["top_predictions"],
        "image_quality": result.get("image_quality", {}),
        "stub_mode": result.get("stub_mode", True),
        "model_version": result["model_version"],
        "created_at": now.isoformat(),
    }


@router.get("/history")
async def get_disease_history(
    page: int = 1,
    page_size: int = 20,
    current_user: dict = Depends(get_current_user),
):
    """Return paginated disease prediction history for the current user."""
    uid = current_user["uid"]
    all_preds = _disease_svc.query(
        "user_id", "==", uid,
        order_by="created_at", descending=True, limit=200,
    )
    total = len(all_preds)
    start = (page - 1) * page_size
    preds = all_preds[start: start + page_size]
    return {"total": total, "page": page, "page_size": page_size, "predictions": preds}


@router.get("/{prediction_id}")
async def get_disease_prediction(
    prediction_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Fetch a single disease prediction by ID."""
    doc = _disease_svc.get(prediction_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Prediction not found.")
    if doc.get("user_id") != current_user["uid"] and current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Access denied.")
    return doc
