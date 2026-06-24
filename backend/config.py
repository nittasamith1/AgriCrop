"""
AgriCrop – Application Configuration
Loads all settings from environment variables (.env file).
Uses pydantic-settings for type-safe config management.
"""

import os
from functools import lru_cache
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import field_validator, AnyHttpUrl


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    All fields map directly to .env.example keys.
    """

    # ── Application ──────────────────────────────────────────
    APP_NAME: str = "AgriCrop"
    APP_ENV: str = "development"
    APP_PORT: int = 8000
    SECRET_KEY: str = "change-this-secret-key-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # ── Firebase Admin SDK ────────────────────────────────────
    FIREBASE_PROJECT_ID: str = ""
    FIREBASE_PRIVATE_KEY_ID: str = ""
    FIREBASE_PRIVATE_KEY: str = ""
    FIREBASE_CLIENT_EMAIL: str = ""
    FIREBASE_CLIENT_ID: str = ""
    FIREBASE_AUTH_URI: str = "https://accounts.google.com/o/oauth2/auth"
    FIREBASE_TOKEN_URI: str = "https://oauth2.googleapis.com/token"
    FIREBASE_SERVICE_ACCOUNT_PATH: str = "./serviceAccountKey.json"

    # ── Firebase Client (for frontend JS config output) ───────
    FIREBASE_API_KEY: str = ""
    FIREBASE_AUTH_DOMAIN: str = ""
    FIREBASE_STORAGE_BUCKET: str = ""
    FIREBASE_MESSAGING_SENDER_ID: str = ""
    FIREBASE_APP_ID: str = ""
    FIREBASE_MEASUREMENT_ID: str = ""

    # ── Firestore ─────────────────────────────────────────────
    FIRESTORE_EMULATOR_HOST: str = ""
    USE_FIRESTORE_EMULATOR: bool = False

    # ── Firebase Storage ──────────────────────────────────────
    FIREBASE_STORAGE_URL: str = ""

    # ── AI Model Paths ────────────────────────────────────────
    DISEASE_MODEL_PATH: str = "./ai_models/saved_models/disease_model.h5"
    SOIL_MODEL_PATH: str = "./ai_models/saved_models/soil_model.h5"
    DISEASE_CLASSES_PATH: str = "./datasets/disease/disease_labels.csv"
    MODEL_CONFIDENCE_THRESHOLD: float = 0.65

    # ── CORS ──────────────────────────────────────────────────
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost:8080"

    @property
    def cors_origins(self) -> List[str]:
        """Parse comma-separated ALLOWED_ORIGINS into a list."""
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",") if o.strip()]

    # ── Rate Limiting ─────────────────────────────────────────
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW_SECONDS: int = 60

    # ── File Upload ───────────────────────────────────────────
    MAX_UPLOAD_SIZE_MB: int = 10
    ALLOWED_IMAGE_EXTENSIONS: str = "jpg,jpeg,png,webp,bmp"
    UPLOAD_TEMP_DIR: str = "./tmp/agricrop_uploads"

    @property
    def allowed_extensions(self) -> List[str]:
        return [e.strip().lower() for e in self.ALLOWED_IMAGE_EXTENSIONS.split(",")]

    @property
    def max_upload_bytes(self) -> int:
        return self.MAX_UPLOAD_SIZE_MB * 1024 * 1024

    # ── Reports ───────────────────────────────────────────────
    REPORTS_BUCKET_PATH: str = "reports/"

    # ── Logging ───────────────────────────────────────────────
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "./logs/agricrop.log"

    # ── Firestore Collection Names (constants) ─────────────────
    COLLECTION_USERS: str = "users"
    COLLECTION_FARMS: str = "farms"
    COLLECTION_PREDICTIONS: str = "predictions"
    COLLECTION_DISEASE_PREDICTIONS: str = "disease_predictions"
    COLLECTION_SOIL_PREDICTIONS: str = "soil_predictions"
    COLLECTION_NOTIFICATIONS: str = "notifications"
    COLLECTION_REPORTS: str = "reports"
    COLLECTION_ACTIVITY_LOGS: str = "activity_logs"

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
        "extra": "ignore"
    }


@lru_cache()
def get_settings() -> Settings:
    """
    Return a cached Settings instance.
    Use dependency injection: Depends(get_settings)
    """
    return Settings()


# Module-level singleton for direct imports
settings = get_settings()
