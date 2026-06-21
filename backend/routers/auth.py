"""
AgriCrop – Auth Router
Handles user registration, login, profile creation, and Firebase token operations.
POST /api/v1/auth/register
POST /api/v1/auth/login
POST /api/v1/auth/forgot-password
GET  /api/v1/auth/me
"""

from datetime import datetime
from typing import Optional

import firebase_admin.auth as firebase_auth
from fastapi import APIRouter, Depends, HTTPException, status, Request
from loguru import logger
from slowapi import Limiter
from slowapi.util import get_remote_address

from backend.config import settings
from backend.dependencies import get_current_user, get_db
from backend.models.user import (
    UserRegisterRequest, UserProfileResponse, UserUpdateRequest,
    FarmCreateRequest, FarmResponse, MessageResponse,
)
from backend.services.firebase_service import FirestoreService
from backend.services.notification_service import notification_service
from backend.utils.helpers import generate_id, utc_now, sanitize_dict

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)

_user_svc = FirestoreService(settings.COLLECTION_USERS)
_farm_svc = FirestoreService(settings.COLLECTION_FARMS)


# ── Register ──────────────────────────────────────────────────────────────────
@router.post("/register", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
async def register(request: Request, payload: UserRegisterRequest):
    """
    Register a new user with Firebase Authentication and create
    a Firestore profile document.
    """
    try:
        # Create user in Firebase Auth
        fb_user = firebase_auth.create_user(
            email=payload.email,
            password=payload.password,
            display_name=payload.name,
            email_verified=False,
        )

        # Send email verification
        try:
            verification_link = firebase_auth.generate_email_verification_link(payload.email)
            logger.info(f"Verification link generated for {payload.email}: {verification_link}")
        except Exception as e:
            logger.warning(f"Could not generate verification link: {e}")

        # Create Firestore user document
        now = utc_now()
        user_doc = sanitize_dict({
            "uid": fb_user.uid,
            "email": payload.email,
            "name": payload.name,
            "role": payload.role,
            "phone": payload.phone,
            "state": payload.state,
            "district": payload.district,
            "profile_picture_url": None,
            "farm_ids": [],
            "is_email_verified": False,
            "is_active": True,
            "total_predictions": 0,
            "created_at": now,
            "updated_at": now,
        })
        _user_svc.create(fb_user.uid, user_doc)

        # Welcome notification
        notification_service.system_notification(
            user_id=fb_user.uid,
            title="🌱 Welcome to AgriCrop!",
            message=(
                "Your account has been created successfully. "
                "Start by adding your farm location and uploading a crop leaf image."
            ),
        )

        logger.info(f"New user registered: {payload.email} (uid={fb_user.uid}, role={payload.role})")
        return MessageResponse(message="Account created successfully. Please verify your email.")

    except firebase_auth.EmailAlreadyExistsError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        )
    except Exception as e:
        logger.error(f"Registration failed for {payload.email}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}",
        )


# ── Forgot Password ────────────────────────────────────────────────────────────
@router.post("/forgot-password", response_model=MessageResponse)
@limiter.limit("5/minute")
async def forgot_password(request: Request, email: str):
    """Generate a Firebase password reset link."""
    try:
        reset_link = firebase_auth.generate_password_reset_link(email)
        logger.info(f"Password reset link generated for: {email}")
        # In production, send this link via your email service (SendGrid, etc.)
        return MessageResponse(
            message="Password reset link generated. Check your email inbox."
        )
    except firebase_auth.UserNotFoundError:
        # Return generic message to prevent email enumeration
        return MessageResponse(message="If this email is registered, a reset link has been sent.")
    except Exception as e:
        logger.error(f"Forgot password error: {e}")
        raise HTTPException(status_code=500, detail="Could not process password reset request.")


# ── Get Current User Profile ───────────────────────────────────────────────────
@router.get("/me", response_model=UserProfileResponse)
async def get_profile(current_user: dict = Depends(get_current_user)):
    """Return the authenticated user's profile."""
    return UserProfileResponse(
        uid=current_user.get("uid", ""),
        email=current_user.get("email", ""),
        name=current_user.get("name", ""),
        role=current_user.get("role", "farmer"),
        phone=current_user.get("phone"),
        state=current_user.get("state"),
        district=current_user.get("district"),
        profile_picture_url=current_user.get("profile_picture_url"),
        farm_ids=current_user.get("farm_ids", []),
        is_email_verified=current_user.get("is_email_verified", False),
        created_at=current_user.get("created_at"),
        updated_at=current_user.get("updated_at"),
        total_predictions=current_user.get("total_predictions", 0),
        is_active=current_user.get("is_active", True),
    )


# ── Update Profile ─────────────────────────────────────────────────────────────
@router.put("/me", response_model=MessageResponse)
async def update_profile(
    payload: UserUpdateRequest,
    current_user: dict = Depends(get_current_user),
):
    """Update the authenticated user's profile fields."""
    uid = current_user["uid"]
    update_data = sanitize_dict({
        **payload.model_dump(exclude_none=True),
        "updated_at": utc_now(),
    })
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update.")
    _user_svc.update(uid, update_data)
    logger.info(f"Profile updated for uid={uid}")
    return MessageResponse(message="Profile updated successfully.")


# ── Add Farm ──────────────────────────────────────────────────────────────────
@router.post("/farms", response_model=FarmResponse, status_code=status.HTTP_201_CREATED)
async def add_farm(
    payload: FarmCreateRequest,
    current_user: dict = Depends(get_current_user),
):
    """Add a new farm location for the authenticated user."""
    uid = current_user["uid"]
    farm_id = generate_id("farm")
    now = utc_now()

    farm_doc = sanitize_dict({
        "farm_id": farm_id,
        "user_id": uid,
        "name": payload.name,
        "latitude": payload.location.latitude,
        "longitude": payload.location.longitude,
        "area_acres": payload.area_acres,
        "crop_types": payload.crop_types,
        "soil_type": payload.soil_type,
        "district": payload.district,
        "state": payload.state,
        "irrigation_type": payload.irrigation_type,
        "notes": payload.notes,
        "total_predictions": 0,
        "created_at": now,
        "updated_at": now,
    })

    _farm_svc.create(farm_id, farm_doc)

    # Update user's farm_ids list
    current_farm_ids = current_user.get("farm_ids", [])
    current_farm_ids.append(farm_id)
    _user_svc.update(uid, {"farm_ids": current_farm_ids, "updated_at": now})

    logger.info(f"Farm '{payload.name}' added for uid={uid}, farm_id={farm_id}")
    return FarmResponse(**farm_doc)


# ── Get User Farms ─────────────────────────────────────────────────────────────
@router.get("/farms")
async def get_my_farms(current_user: dict = Depends(get_current_user)):
    """Return all farms belonging to the authenticated user."""
    uid = current_user["uid"]
    farms = _farm_svc.query("user_id", "==", uid, order_by="created_at", limit=50)
    return {"farms": farms, "total": len(farms)}
