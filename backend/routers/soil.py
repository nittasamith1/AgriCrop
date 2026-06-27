"""
AgriCrop – Soil Prediction Router
POST /api/v1/soil/predict   – Predict soil moisture from environmental inputs
GET  /api/v1/soil/history   – Get soil prediction history
GET  /api/v1/soil/{id}      – Get single soil prediction by ID
"""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from loguru import logger
from slowapi import Limiter
from slowapi.util import get_remote_address

from backend.config import settings
from backend.dependencies import get_current_user
from backend.ai.soil_predictor import soil_predictor
from backend.ai.recommendation_engine import get_irrigation_recommendation
from backend.models.prediction import SoilPredictionRequest
from backend.services.firebase_service import FirestoreService
from backend.services.notification_service import notification_service
from backend.utils.helpers import generate_id, utc_now

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)

_soil_svc = FirestoreService(settings.COLLECTION_SOIL_PREDICTIONS)
_user_svc = FirestoreService(settings.COLLECTION_USERS)
_farm_svc = FirestoreService(settings.COLLECTION_FARMS)


@router.post("/predict", status_code=status.HTTP_201_CREATED)
@limiter.limit("30/minute")
async def predict_soil(
    request: Request,
    payload: SoilPredictionRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    Predict soil moisture percentage from environmental features.
    Returns moisture level, water requirement, and irrigation recommendation.
    """
    uid = current_user["uid"]

    # ── Validate soil type ────────────────────────────────────────────────────
    valid_soil_types = {"sandy", "loamy", "clay", "silt", "peaty"}
    if payload.soil_type.lower() not in valid_soil_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid soil_type. Must be one of: {', '.join(valid_soil_types)}",
        )

    # ── Run Prediction ────────────────────────────────────────────────────────
    try:
        result = soil_predictor.predict(payload)
    except Exception as e:
        logger.error(f"Soil prediction failed: {e}")
        raise HTTPException(status_code=500, detail="Soil prediction failed. Please try again.")

    # ── Get farm location ─────────────────────────────────────────────────────
    farm_lat, farm_lon, district, state = payload.latitude, payload.longitude, None, None
    if payload.farm_id:
        farm_doc = _farm_svc.get(payload.farm_id)
        if farm_doc and farm_doc.get("user_id") == uid:
            farm_lat = farm_lat or farm_doc.get("latitude")
            farm_lon = farm_lon or farm_doc.get("longitude")
            district = farm_doc.get("district")
            state = farm_doc.get("state")
            # Update farm's last known moisture
            _farm_svc.update(payload.farm_id, {
                "last_moisture": result["predicted_moisture"],
                "updated_at": utc_now(),
            })

    # ── Build recommendation text ─────────────────────────────────────────────
    recommendation = get_irrigation_recommendation(
        predicted_moisture=result["predicted_moisture"]
    )
    recommendation_text = recommendation["message"]

    # ── Save to Firestore ─────────────────────────────────────────────────────
    prediction_id = generate_id("spred")
    now = utc_now()

    prediction_doc = {
        "prediction_id": prediction_id,
        "user_id": uid,
        "farm_id": payload.farm_id,
        "predicted_moisture": result["predicted_moisture"],
        "field_capacity": result["field_capacity"],
        "wilting_point": result["wilting_point"],
        "available_water_content": result["available_water_content"],
        "water_requirement_mm": result["water_requirement_mm"],
        "irrigation_recommended": result["irrigation_recommended"],
        "irrigation_type": result["irrigation_type"],
        "next_irrigation_hours": result["next_irrigation_hours"],
        "recommendation_text": recommendation_text,
        "input_features": result["input_features"],
        "latitude": farm_lat,
        "longitude": farm_lon,
        "district": district,
        "state": state,
        "stub_mode": result.get("stub_mode", True),
        "model_version": result["model_version"],
        "created_at": now,
    }

    _soil_svc.create(prediction_id, prediction_doc)

    # Increment total_predictions
    total = current_user.get("total_predictions", 0) + 1
    _user_svc.update(uid, {"total_predictions": total, "updated_at": now})

    # ── Notification ──────────────────────────────────────────────────────────
    notification_service.soil_alert(
        user_id=uid,
        moisture_percent=result["predicted_moisture"],
        prediction_id=prediction_id,
    )

    logger.info(
        f"Soil prediction: uid={uid} | moisture={result['predicted_moisture']:.1f}% "
        f"| irrigation={result['irrigation_recommended']} | pred_id={prediction_id}"
    )

    return {
        "success": True,
        "prediction_id": prediction_id,
        "predicted_moisture": result["predicted_moisture"],
        "field_capacity": result["field_capacity"],
        "wilting_point": result["wilting_point"],
        "available_water_content": result["available_water_content"],
        "water_requirement_mm": result["water_requirement_mm"],
        "irrigation_recommended": result["irrigation_recommended"],
        "irrigation_type": result["irrigation_type"],
        "next_irrigation_hours": result["next_irrigation_hours"],
        "recommendation_text": recommendation_text,
        "input_features": result["input_features"],
        "stub_mode": result.get("stub_mode", True),
        "model_version": result["model_version"],
        "created_at": now.isoformat(),
    }


@router.get("/history")
async def get_soil_history(
    page: int = 1,
    page_size: int = 20,
    current_user: dict = Depends(get_current_user),
):
    """Return paginated soil prediction history for the current user."""
    uid = current_user["uid"]
    all_preds = _soil_svc.query(
        "user_id", "==", uid,
        order_by="created_at", descending=True, limit=200,
    )
    total = len(all_preds)
    start = (page - 1) * page_size
    preds = all_preds[start: start + page_size]
    return {"total": total, "page": page, "page_size": page_size, "predictions": preds}


@router.get("/{prediction_id}")
async def get_soil_prediction(
    prediction_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Fetch a single soil prediction by ID."""
    doc = _soil_svc.get(prediction_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Prediction not found.")
    if doc.get("user_id") != current_user["uid"] and current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Access denied.")
    return doc
