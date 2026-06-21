"""
AgriCrop – Input Validators
Reusable validation functions for file uploads, coordinates,
soil inputs, and request payloads.
"""

import os
import re
from typing import Optional, Tuple
from fastapi import UploadFile, HTTPException, status
from loguru import logger

from backend.config import settings

# ── Image Upload Validation ────────────────────────────────────────────────────

async def validate_image_upload(file: UploadFile) -> bytes:
    """
    Validate an uploaded image file:
    - Checks MIME type
    - Checks file extension
    - Checks file size limit
    Returns file content bytes if valid.
    Raises HTTPException on failure.
    """
    if file is None or file.filename is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No file uploaded.",
        )

    # Check extension
    ext = os.path.splitext(file.filename)[-1].lstrip(".").lower()
    if ext not in settings.allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"File type '.{ext}' not allowed. Allowed: {', '.join(settings.allowed_extensions)}",
        )

    # Check MIME type
    allowed_mimes = {
        "image/jpeg", "image/jpg", "image/png",
        "image/webp", "image/bmp",
    }
    if file.content_type not in allowed_mimes:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Invalid MIME type '{file.content_type}'. Only images are allowed.",
        )

    # Read and check size
    content = await file.read()
    if len(content) > settings.max_upload_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Maximum size: {settings.MAX_UPLOAD_SIZE_MB} MB.",
        )

    if len(content) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty.",
        )

    return content


# ── Coordinate Validation ──────────────────────────────────────────────────────

def validate_coordinates(lat: float, lon: float) -> Tuple[float, float]:
    """
    Validate latitude and longitude values.
    Raises HTTPException if out of range.
    """
    if not (-90 <= lat <= 90):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid latitude {lat}. Must be between -90 and 90.",
        )
    if not (-180 <= lon <= 180):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid longitude {lon}. Must be between -180 and 180.",
        )
    return lat, lon


# ── Soil Type Validation ───────────────────────────────────────────────────────

VALID_SOIL_TYPES = {"sandy", "loamy", "clay", "silt", "peaty"}

def validate_soil_type(soil_type: str) -> str:
    """Validate that soil_type is one of the recognized categories."""
    normalized = soil_type.strip().lower()
    if normalized not in VALID_SOIL_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid soil_type '{soil_type}'. Must be one of: {', '.join(VALID_SOIL_TYPES)}",
        )
    return normalized


# ── Pagination Validation ──────────────────────────────────────────────────────

def validate_pagination(page: int, page_size: int) -> Tuple[int, int]:
    """Ensure page and page_size are within sensible bounds."""
    if page < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="'page' must be >= 1.",
        )
    if not (1 <= page_size <= 100):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="'page_size' must be between 1 and 100.",
        )
    return page, page_size


# ── UID Validation ─────────────────────────────────────────────────────────────

def validate_uid(uid: str) -> str:
    """Basic Firebase UID format check (28 chars, alphanumeric)."""
    if not re.match(r"^[a-zA-Z0-9]{20,128}$", uid):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID format.",
        )
    return uid
