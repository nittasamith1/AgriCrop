"""
AgriCrop – Auth Middleware
Provides Firebase token verification as middleware and utility functions
for extracting user context from requests.
"""

from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from loguru import logger
import firebase_admin.auth as firebase_auth

# Routes that do NOT require authentication
PUBLIC_ROUTES = {
    "/",
    "/api/health",
    "/api/docs",
    "/api/redoc",
    "/api/openapi.json",
    "/api/v1/auth/register",
    "/api/v1/auth/login",
    "/api/v1/auth/forgot-password",
    "/api/v1/auth/verify-email",
}


class FirebaseAuthMiddleware(BaseHTTPMiddleware):
    """
    Optional middleware that attaches the decoded Firebase token
    to request.state.user for downstream use.
    This does NOT enforce auth — use Depends(get_current_user) for that.
    """

    async def dispatch(self, request: Request, call_next):
        request.state.user = None
        auth_header = request.headers.get("Authorization", "")

        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
            try:
                decoded = firebase_auth.verify_id_token(token, check_revoked=True)
                request.state.user = decoded
            except Exception as e:
                # Not raising here — protected routes handle it via Depends
                logger.debug(f"Token pre-verification failed (non-critical): {e}")

        response = await call_next(request)
        return response


def extract_uid_from_request(request: Request) -> str:
    """
    Extract the Firebase UID from the request state set by middleware.
    Raises 401 if not authenticated.
    """
    user = getattr(request.state, "user", None)
    if not user or not user.get("uid"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required.",
        )
    return user["uid"]
