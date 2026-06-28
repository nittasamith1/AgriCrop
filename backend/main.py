"""
AgriCrop – FastAPI Application Entry Point
Configures middleware, routers, CORS, rate limiting, and database lifespan events.
Firebase completely removed. MongoDB Atlas + GridFS + JWT only.
"""

import os
import sys
from contextlib import asynccontextmanager
from loguru import logger

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from backend.config import settings
from backend.database import db
from backend.routers import auth, disease, soil, map_router, history, notifications, reports, admin, files

# ── Logging Setup ─────────────────────────────────────────────────────────────
os.makedirs("logs", exist_ok=True)
os.makedirs(settings.UPLOAD_TEMP_DIR, exist_ok=True)
logger.remove()
logger.add(sys.stderr, level=settings.LOG_LEVEL, colorize=True,
           format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>")
try:
    logger.add(settings.LOG_FILE, rotation="10 MB", retention="30 days", level=settings.LOG_LEVEL, enqueue=True)
except Exception:
    pass  # Log file may not be writable on Render — stdout is fine

# ── Rate Limiter ──────────────────────────────────────────────────────────────
limiter = Limiter(key_func=get_remote_address, default_limits=[
    f"{settings.RATE_LIMIT_REQUESTS}/{settings.RATE_LIMIT_WINDOW_SECONDS}seconds"
])


# ── Lifespan ──────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events for MongoDB client connection."""
    logger.info("🌱 AgriCrop API starting up...")
    try:
        await db.connect()
        logger.info("✅ Database client connected and indexed")
    except Exception as e:
        logger.critical(f"❌ Database connection failed: {e}")
        # In production we crash. In development we might want to continue, but MongoDB is critical.
        raise e
        
    # Create upload temp directory
    os.makedirs(settings.UPLOAD_TEMP_DIR, exist_ok=True)
    logger.info(f"✅ Upload temp dir ready: {settings.UPLOAD_TEMP_DIR}")
    yield
    await db.disconnect()
    logger.info("👋 AgriCrop API shutting down...")


# ── FastAPI App ───────────────────────────────────────────────────────────────
app = FastAPI(
    title="AgriCrop API",
    description=(
        "AI-powered Precision Agriculture API for Plant Disease Detection, "
        "Soil Moisture Prediction, and Geospatial Crop Health Monitoring.\n\n"
        "## Authentication\n"
        "Use the **Authorize** button. In the **HTTPBearer** field paste only the **raw JWT token** "
        "(without the word \"Bearer\"). FastAPI adds `Bearer ` automatically."
    ),
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
    # Swagger UI OAuth2 config for the Authorize button
    swagger_ui_oauth2_redirect_url="/api/docs/oauth2-redirect",
)

# ── Rate Limiter State ────────────────────────────────────────────────────────
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ── CORS Middleware ───────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?|https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# ── Static Files Mount ────────────────────────────────────────────────────────
# In case of local upload testing fallback
try:
    app.mount("/static/uploads", StaticFiles(directory=settings.UPLOAD_TEMP_DIR), name="uploads")
except Exception as e:
    logger.warning(f"Could not mount static files: {e}")


# ── Request Logging Middleware ────────────────────────────────────────────────
@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"→ {request.method} {request.url.path}")
    response = await call_next(request)
    logger.info(f"← {response.status_code} {request.url.path}")
    return response


# ── Global Exception Handler ──────────────────────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception on {request.url.path}: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred. Please try again later."}
    )


# ── Routers ───────────────────────────────────────────────────────────────────
API_PREFIX = "/api/v1"

app.include_router(auth.router,          prefix=f"{API_PREFIX}/auth",          tags=["Authentication"])
app.include_router(disease.router,       prefix=f"{API_PREFIX}/disease",       tags=["Disease Detection"])
app.include_router(soil.router,          prefix=f"{API_PREFIX}/soil",          tags=["Soil Prediction"])
app.include_router(map_router.router,    prefix=f"{API_PREFIX}/map",            tags=["GIS Map"])
app.include_router(history.router,       prefix=f"{API_PREFIX}/history",        tags=["Prediction History"])
app.include_router(notifications.router, prefix=f"{API_PREFIX}/notifications",  tags=["Notifications"])
app.include_router(reports.router,       prefix=f"{API_PREFIX}/reports",        tags=["Reports"])
app.include_router(admin.router,         prefix=f"{API_PREFIX}/admin",          tags=["Admin"])
app.include_router(files.router,         prefix=f"{API_PREFIX}/files",          tags=["GridFS Storage"])


# ── Health Check ──────────────────────────────────────────────────────────────
@app.get("/api/health", tags=["Health"])
async def health_check():
    """Endpoint checking system connectivity and health status."""
    db_ok = False
    try:
        await db.client.admin.command('ping')
        db_ok = True
    except Exception:
        pass
        
    return {
        "status": "healthy" if db_ok else "unhealthy",
        "app": settings.APP_NAME,
        "version": "1.0.0",
        "database": "connected" if db_ok else "disconnected",
        "environment": settings.APP_ENV,
    }


@app.get("/", tags=["Root"])
async def root():
    return {
        "message": f"Welcome to {settings.APP_NAME} API",
        "docs": "/api/docs",
        "health": "/api/health",
    }
