"""
AgriCrop – Firebase Storage Service
Handles image uploads, PDF storage, and file management.
"""

import os
import uuid
from datetime import datetime
from typing import Optional
from loguru import logger
import firebase_admin.storage as fb_storage

from backend.config import settings
from backend.utils.helpers import utc_now


class StorageService:
    """Manages file uploads to Firebase Storage or local fallback."""

    def __init__(self):
        self.bucket = None
        self._init_bucket()

    def _init_bucket(self):
        """Initialize Firebase Storage bucket."""
        try:
            self.bucket = fb_storage.bucket(settings.FIREBASE_STORAGE_BUCKET)
            logger.info(f"✅ Storage bucket initialized: {settings.FIREBASE_STORAGE_BUCKET}")
        except Exception as e:
            logger.warning(f"Storage bucket initialization failed: {e}. Using local fallback.")
            self.bucket = None

    def upload_leaf_image(
        self,
        content: bytes,
        filename: str,
        user_id: str,
        content_type: str = "image/jpeg",
    ) -> str:
        """
        Upload a leaf image to Firebase Storage or local storage.
        Returns the URL.
        """
        try:
            # Generate unique filename
            ext = filename.split(".")[-1].lower()
            unique_name = f"{user_id}/leaves/{uuid.uuid4().hex}.{ext}"

            if self.bucket:
                # Upload to Firebase Storage
                blob = self.bucket.blob(unique_name)
                blob.upload_from_string(content, content_type=content_type)
                blob.make_public()
                url = blob.public_url
                logger.info(f"✅ Leaf image uploaded: {unique_name}")
                return url
            else:
                # Fallback to local storage
                return self._save_locally(content, unique_name)

        except Exception as e:
            logger.error(f"Image upload failed: {e}")
            raise

    def upload_report_pdf(
        self,
        content: bytes,
        filename: str,
        user_id: str,
    ) -> str:
        """
        Upload a PDF report to Firebase Storage or local storage.
        Returns the URL.
        """
        try:
            unique_name = f"{user_id}/reports/{uuid.uuid4().hex}_{filename}"

            if self.bucket:
                blob = self.bucket.blob(unique_name)
                blob.upload_from_string(content, content_type="application/pdf")
                url = blob.public_url
                logger.info(f"✅ PDF report uploaded: {unique_name}")
                return url
            else:
                return self._save_locally(content, unique_name)

        except Exception as e:
            logger.error(f"PDF upload failed: {e}")
            raise

    def _save_locally(self, content: bytes, path: str) -> str:
        """
        Save file to local storage (fallback).
        """
        try:
            local_path = os.path.join(settings.UPLOAD_TEMP_DIR, path)
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            
            with open(local_path, "wb") as f:
                f.write(content)
            
            # Return URL pointing to static endpoint
            url = f"{os.environ.get('API_BASE', 'http://localhost:8000')}/static/uploads/{path}"
            logger.info(f"✅ File saved locally: {local_path}")
            return url
        except Exception as e:
            logger.error(f"Local file save failed: {e}")
            raise

    def delete_file(self, path: str) -> bool:
        """
        Delete a file from storage.
        """
        try:
            if self.bucket:
                blob = self.bucket.blob(path)
                blob.delete()
                logger.info(f"✅ File deleted: {path}")
            else:
                local_path = os.path.join(settings.UPLOAD_TEMP_DIR, path)
                if os.path.exists(local_path):
                    os.remove(local_path)
                    logger.info(f"✅ Local file deleted: {local_path}")
            return True
        except Exception as e:
            logger.error(f"File deletion failed: {e}")
            return False


# Singleton instance
storage_service = StorageService()
