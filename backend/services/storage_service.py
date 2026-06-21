"""
AgriCrop – Firebase Storage Service
Handles image and report uploads/downloads via Firebase Storage.
"""

import os
import uuid
from typing import Optional
from datetime import timedelta

from firebase_admin import storage as fb_storage
from loguru import logger

from backend.config import settings
from backend.utils.helpers import hash_file


class StorageService:
    """
    Thin wrapper around Firebase Cloud Storage for AgriCrop.
    Handles leaf image uploads, report uploads, and signed URL generation.
    """

    LEAF_IMAGE_PREFIX = "leaf_images/"
    REPORT_PREFIX = "reports/"
    PROFILE_PIC_PREFIX = "profile_pictures/"

    def _get_bucket(self):
        return fb_storage.bucket()

    def upload_leaf_image(
        self,
        content: bytes,
        filename: str,
        user_id: str,
        content_type: str = "image/jpeg",
    ) -> str:
        """
        Upload a leaf image to Firebase Storage.
        Returns the public download URL.
        """
        ext = os.path.splitext(filename)[-1].lower() or ".jpg"
        unique_name = f"{self.LEAF_IMAGE_PREFIX}{user_id}/{uuid.uuid4().hex}{ext}"

        bucket = self._get_bucket()
        blob = bucket.blob(unique_name)
        blob.upload_from_string(content, content_type=content_type)
        blob.make_public()

        logger.info(f"Uploaded leaf image: {unique_name}")
        return blob.public_url

    def upload_report_pdf(
        self,
        content: bytes,
        report_id: str,
        user_id: str,
    ) -> str:
        """
        Upload a generated PDF report to Firebase Storage.
        Returns a signed URL valid for 7 days.
        """
        blob_name = f"{self.REPORT_PREFIX}{user_id}/{report_id}.pdf"
        bucket = self._get_bucket()
        blob = bucket.blob(blob_name)
        blob.upload_from_string(content, content_type="application/pdf")

        url = blob.generate_signed_url(
            expiration=timedelta(days=7),
            method="GET",
        )
        logger.info(f"Uploaded report PDF: {blob_name}")
        return url

    def upload_profile_picture(
        self,
        content: bytes,
        user_id: str,
        content_type: str = "image/jpeg",
    ) -> str:
        """Upload a user profile picture and return its public URL."""
        ext = ".jpg" if "jpeg" in content_type else ".png"
        blob_name = f"{self.PROFILE_PIC_PREFIX}{user_id}/avatar{ext}"
        bucket = self._get_bucket()
        blob = bucket.blob(blob_name)
        blob.upload_from_string(content, content_type=content_type)
        blob.make_public()
        logger.info(f"Uploaded profile picture: {blob_name}")
        return blob.public_url

    def delete_file(self, blob_name: str) -> bool:
        """Delete a file from Firebase Storage by its blob path."""
        try:
            bucket = self._get_bucket()
            blob = bucket.blob(blob_name)
            blob.delete()
            logger.info(f"Deleted storage blob: {blob_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete blob '{blob_name}': {e}")
            return False

    def get_signed_url(self, blob_name: str, expiry_hours: int = 1) -> Optional[str]:
        """Generate a time-limited signed URL for a private blob."""
        try:
            bucket = self._get_bucket()
            blob = bucket.blob(blob_name)
            url = blob.generate_signed_url(
                expiration=timedelta(hours=expiry_hours),
                method="GET",
            )
            return url
        except Exception as e:
            logger.error(f"Signed URL generation failed for '{blob_name}': {e}")
            return None


# Module-level singleton
storage_service = StorageService()
