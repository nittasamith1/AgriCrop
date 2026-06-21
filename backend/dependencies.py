"""
AgriCrop – Shared FastAPI Dependencies
Provides reusable dependency-injected services:
  - Firebase auth token verification
  - Current user retrieval
  - Admin role guard
  - Database client
"""

from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import firebase_admin.auth as firebase_auth
from loguru import logger

from backend.config import settings
from backend.services.firebase_service import get_firestore_client

# ── HTTP Bearer Scheme ────────────────────────────────────────────────────────
bearer_scheme = HTTPBearer(auto_error=False)


# ── Token Verification ────────────────────────────────────────────────────────
async def verify_firebase_token(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
) -> dict:
    """
    Verify a Firebase ID token from the Authorization header.
    Returns the decoded token payload (uid, email, role, etc.).
    Raises 401 if missing or invalid.
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing. Please include 'Bearer <token>'.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    try:
        decoded = firebase_auth.verify_id_token(token, check_revoked=True)
        return decoded
    except firebase_auth.RevokedIdTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked. Please log in again.",
        )
    except firebase_auth.ExpiredIdTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired. Please log in again.",
        )
    except firebase_auth.InvalidIdTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}",
        )
    except Exception as e:
        logger.error(f"Token verification error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not verify authentication token.",
        )


async def get_current_user(
    token_data: dict = Depends(verify_firebase_token),
) -> dict:
    """
    Returns the verified token payload enriched with Firestore user profile.
    Exposes: uid, email, name, role, farm_ids, etc.
    """
    uid = token_data.get("uid")
    if not uid:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="UID not found in token.")

    db = get_firestore_client()
    user_ref = db.collection(settings.COLLECTION_USERS).document(uid)
    user_doc = user_ref.get()

    if not user_doc.exists:
        # Return token data only (user not yet saved to Firestore)
        return {
            "uid": uid,
            "email": token_data.get("email", ""),
            "name": token_data.get("name", ""),
            "role": "farmer",
            "is_new": True,
        }

    user_data = user_doc.to_dict()
    user_data["uid"] = uid
    return user_data


async def require_admin(
    current_user: dict = Depends(get_current_user),
) -> dict:
    """
    Guards admin-only routes. Raises 403 if the user is not an admin.
    """
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required to access this resource.",
        )
    return current_user


def get_db():
    """Dependency that yields a Firestore client."""
    return get_firestore_client()
