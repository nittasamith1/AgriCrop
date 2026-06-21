"""
AgriCrop – General Utility Helpers
Reusable utility functions used across backend modules.
"""

import uuid
import hashlib
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from loguru import logger


def generate_id(prefix: str = "") -> str:
    """Generate a unique ID with optional prefix."""
    uid = str(uuid.uuid4()).replace("-", "")
    return f"{prefix}_{uid}" if prefix else uid


def utc_now() -> datetime:
    """Return the current UTC datetime (timezone-aware)."""
    return datetime.now(tz=timezone.utc)


def utc_now_iso() -> str:
    """Return current UTC datetime as ISO 8601 string."""
    return utc_now().isoformat()


def severity_from_confidence(confidence: float) -> str:
    """
    Map a disease detection confidence score to a severity label.
    Used for disease predictions when the disease is not 'Healthy'.
    """
    if confidence < 0.50:
        return "mild"
    elif confidence < 0.75:
        return "moderate"
    else:
        return "severe"


def marker_color_from_severity(severity: str) -> str:
    """Return a CSS/Leaflet color string based on severity."""
    mapping = {
        "healthy": "green",
        "mild": "yellow",
        "moderate": "orange",
        "severe": "red",
    }
    return mapping.get(severity.lower(), "grey")


def sanitize_dict(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Remove None values from a dictionary (for Firestore writes).
    Firestore does not accept Python None as a field value in some contexts.
    """
    return {k: v for k, v in data.items() if v is not None}


def paginate(items: List[Any], page: int = 1, page_size: int = 20) -> Dict[str, Any]:
    """
    Simple in-memory pagination helper.
    Returns a dict with total, page, page_size, and items.
    """
    page = max(1, page)
    page_size = max(1, min(page_size, 100))
    total = len(items)
    start = (page - 1) * page_size
    end = start + page_size
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": items[start:end],
    }


def hash_file(content: bytes) -> str:
    """Return SHA256 hex digest of file bytes (for deduplication)."""
    return hashlib.sha256(content).hexdigest()


def format_bytes(size_bytes: int) -> str:
    """Human-readable file size string."""
    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"


def build_firestore_doc(data: Dict[str, Any], exclude_none: bool = True) -> Dict[str, Any]:
    """Prepare a dict for Firestore write — removes None, serializes datetimes."""
    result = {}
    for k, v in data.items():
        if exclude_none and v is None:
            continue
        if isinstance(v, datetime):
            result[k] = v
        else:
            result[k] = v
    return result


def clamp(value: float, min_val: float, max_val: float) -> float:
    """Clamp a float value between min and max."""
    return max(min_val, min(max_val, value))
