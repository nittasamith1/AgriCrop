"""
AgriCrop – Application Configuration
Loads all settings from environment variables (.env file).
Uses pydantic-settings for type-safe config management.
Firebase completely removed. MongoDB Atlas + JWT + SMTP only.
"""

import os
from functools import lru_cache
from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    All fields map directly to .env / .env.example keys.
    """

    # ── Application ──────────────────────────────────────────
    APP_NAME: str = "AgriCrop"
    APP_ENV: str = "development"
    APP_PORT: int = 8000
    FRONTEND_URL: str = "http://localhost:8080"

    # ── Security ─────────────────────────────────────────────
    SECRET_KEY: str = "change-this-secret-key-in-production-use-64-chars"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # ── MongoDB Atlas ─────────────────────────────────────────
    MONGODB_URI: str = os.getenv(
    "MONGODB_URI",
    "mongodb+srv://db_user:3gWRpw4tTssyTR8Z@cluster0.xdax7ct.mongodb.net/?appName=Cluster0"
    )
    MONGODB_DB_NAME: str = "agricrop"

    # ── MongoDB Collection Names ──────────────────────────────
    COLLECTION_USERS: str = "users"
    COLLECTION_FARMS: str = "farms"
    COLLECTION_DISEASE_PREDICTIONS: str = "disease_predictions"
    COLLECTION_SOIL_PREDICTIONS: str = "soil_predictions"
    COLLECTION_PREDICTIONS: str = "predictions"
    COLLECTION_NOTIFICATIONS: str = "notifications"
    COLLECTION_REPORTS: str = "reports"
    COLLECTION_ANALYTICS: str = "analytics"
    COLLECTION_ACTIVITY_LOGS: str = "activity_logs"
    COLLECTION_ADMIN_LOGS: str = "admin_logs"
    COLLECTION_SETTINGS: str = "settings"
    COLLECTION_REFRESH_TOKENS: str = "refresh_tokens"
    COLLECTION_RESET_TOKENS: str = "reset_tokens"

    # ── SMTP Email ────────────────────────────────────────────
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    FROM_EMAIL: str = "noreply@agricrop.app"
    FROM_NAME: str = "AgriCrop"
    EMAIL_ENABLED: bool = False  # Set True in production with valid SMTP creds

    # ── AI Model Paths ────────────────────────────────────────
    DISEASE_MODEL_PATH: str = "./ai_models/saved_models/disease_model.h5"
    SOIL_MODEL_PATH: str = "./ai_models/saved_models/soil_model.h5"
    DISEASE_CLASSES_PATH: str = "./datasets/disease/disease_labels.csv"
    MODEL_CONFIDENCE_THRESHOLD: float = 0.65

    # ── CORS ──────────────────────────────────────────────────
    ALLOWED_ORIGINS: str = (
        "http://localhost:3000,http://localhost:8000,http://localhost:8080,"
        "http://127.0.0.1:3000,http://127.0.0.1:8000,http://127.0.0.1:8080,"
        "https://agricrop.vercel.app"
    )

    @property
    def cors_origins(self) -> List[str]:
        """Parse comma-separated ALLOWED_ORIGINS into a list.
        NOTE: Do NOT include '*' when allow_credentials=True (FastAPI restriction).
        If '*' is set (e.g. from Render env var), expand it to known safe origins.
        """
        raw = self.ALLOWED_ORIGINS.strip()
        # If wildcard is set, fall back to permissive but valid origins list
        if raw == "*":
            return [
                "http://localhost:3000", "http://localhost:8000", "http://localhost:8080",
                "http://127.0.0.1:8080",
                "https://agricrop.vercel.app",
            ]
        origins = [o.strip() for o in raw.split(",") if o.strip() and o.strip() != "*"]
        return origins if origins else ["http://localhost:8080"]

    # ── Rate Limiting ─────────────────────────────────────────
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW_SECONDS: int = 60

    # ── File Upload ───────────────────────────────────────────
    MAX_UPLOAD_SIZE_MB: int = 10
    ALLOWED_IMAGE_EXTENSIONS: str = "jpg,jpeg,png,webp,bmp"
    # Use /tmp on Render (ephemeral but always exists); local fallback to ./tmp
    UPLOAD_TEMP_DIR: str = "/tmp/agricrop_uploads"

    @property
    def allowed_extensions(self) -> List[str]:
        return [e.strip().lower() for e in self.ALLOWED_IMAGE_EXTENSIONS.split(",")]

    @property
    def max_upload_bytes(self) -> int:
        return self.MAX_UPLOAD_SIZE_MB * 1024 * 1024

    # ── Logging ───────────────────────────────────────────────
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "./logs/agricrop.log"

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
        "extra": "ignore",
    }


@lru_cache()
def get_settings() -> Settings:
    """Return a cached Settings instance."""
    return Settings()


# Module-level singleton for direct imports
settings = get_settings()
