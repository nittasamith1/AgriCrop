"""
AgriCrop – History Router
GET /api/v1/history           – Combined disease + soil prediction history
GET /api/v1/history/dashboard – Summary stats for dashboard
"""

from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, Query
from loguru import logger

from backend.config import settings
from backend.dependencies import get_current_user
from backend.services.mongodb_service import MongoDBService

router = APIRouter()

_disease_svc = MongoDBService(settings.COLLECTION_DISEASE_PREDICTIONS, id_field="prediction_id")
_soil_svc = MongoDBService(settings.COLLECTION_SOIL_PREDICTIONS, id_field="prediction_id")
_user_svc = MongoDBService(settings.COLLECTION_USERS, id_field="uid")
_farm_svc = MongoDBService(settings.COLLECTION_FARMS, id_field="farm_id")


@router.get("/")
async def get_combined_history(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    prediction_type: str = Query(default="all", description="all | disease | soil"),
    current_user: dict = Depends(get_current_user),
):
    """
    Return paginated combined prediction history (disease + soil).
    Sorted by creation time, newest first.
    """
    uid = current_user["uid"]
    result = {"total": 0, "page": page, "page_size": page_size, "disease_predictions": [], "soil_predictions": []}

    if prediction_type in ("all", "disease"):
        d_preds = await _disease_svc.query("user_id", "==", uid, order_by="created_at", descending=True, limit=200)
        d_total = len(d_preds)
        start = (page - 1) * page_size
        result["disease_predictions"] = d_preds[start: start + page_size]
        result["disease_total"] = d_total

    if prediction_type in ("all", "soil"):
        s_preds = await _soil_svc.query("user_id", "==", uid, order_by="created_at", descending=True, limit=200)
        s_total = len(s_preds)
        start = (page - 1) * page_size
        result["soil_predictions"] = s_preds[start: start + page_size]
        result["soil_total"] = s_total

    result["total"] = result.get("disease_total", 0) + result.get("soil_total", 0)
    return result


@router.get("/dashboard")
async def get_dashboard_stats(current_user: dict = Depends(get_current_user)):
    """
    Return summary statistics for the user dashboard.
    Includes total predictions, severity breakdown, monthly counts,
    recent predictions, and farms summary.
    """
    uid = current_user["uid"]

    # Fetch predictions and farms
    d_preds = await _disease_svc.query("user_id", "==", uid, order_by="created_at", descending=True, limit=200)
    s_preds = await _soil_svc.query("user_id", "==", uid, order_by="created_at", descending=True, limit=200)
    farms = await _farm_svc.query("user_id", "==", uid, limit=50)

    # Severity breakdown
    severity_counts = {"healthy": 0, "mild": 0, "moderate": 0, "severe": 0}
    crop_disease_map: dict = {}
    for p in d_preds:
        sev = p.get("severity", "unknown")
        if sev in severity_counts:
            severity_counts[sev] += 1
        crop = p.get("crop_type") or "Unknown"
        disease = p.get("disease_name") or "Unknown"
        if crop not in crop_disease_map:
            crop_disease_map[crop] = {}
        crop_disease_map[crop][disease] = crop_disease_map[crop].get(disease, 0) + 1

    # Monthly counts (last 6 months)
    now = datetime.now(tz=timezone.utc)
    monthly_disease = {}
    monthly_soil = {}
    for i in range(6):
        month_key = (now - timedelta(days=30 * i)).strftime("%Y-%m")
        monthly_disease[month_key] = 0
        monthly_soil[month_key] = 0

    def _parse_created_at(created) -> str:
        """Parse created_at to YYYY-MM string regardless of whether it's a datetime or ISO string."""
        if not created:
            return ""
        if hasattr(created, "strftime"):
            return created.strftime("%Y-%m")
        if isinstance(created, str):
            try:
                return created[:7]  # 'YYYY-MM'
            except Exception:
                return ""
        return ""

    for p in d_preds:
        key = _parse_created_at(p.get("created_at"))
        if key in monthly_disease:
            monthly_disease[key] += 1

    for p in s_preds:
        key = _parse_created_at(p.get("created_at"))
        if key in monthly_soil:
            monthly_soil[key] += 1

    # Irrigation stats
    irrigation_count = sum(1 for p in s_preds if p.get("irrigation_recommended"))
    avg_moisture = (
        sum(p.get("predicted_moisture") or 0 for p in s_preds) / len(s_preds)
        if s_preds else 0
    )

    return {
        "total_disease_predictions": len(d_preds),
        "total_soil_predictions": len(s_preds),
        "total_predictions": len(d_preds) + len(s_preds),
        "total_farms": len(farms),
        "severity_breakdown": severity_counts,
        "healthy_count": severity_counts["healthy"],
        "diseased_count": sum(v for k, v in severity_counts.items() if k != "healthy"),
        "irrigation_needed_count": irrigation_count,
        "average_soil_moisture": round(avg_moisture, 1),
        "monthly_disease_counts": monthly_disease,
        "monthly_soil_counts": monthly_soil,
        "crop_disease_distribution": crop_disease_map,
        "recent_disease_predictions": d_preds[:5],
        "recent_soil_predictions": s_preds[:5],
        "farms": farms[:10],
    }
