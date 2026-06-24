"""
AgriCrop – Firebase Storage Service
Handles image and report uploads/downloads via Firebase Storage.
"""

import os
import uuid
from typing import Optional
from datetime import timedelta, datetime

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

    def _make_blob_public(self, blob) -> str:
        """
        Try to make a blob public. Falls back to a long-lived signed URL
        if uniform bucket-level access is enabled (which disables make_public).
        Returns the public URL string.
        """
        # Attempt 1: make_public() — works if fine-grained access is enabled
        try:
            blob.make_public()
            return blob.public_url
        except Exception as e:
            logger.warning(f"make_public() failed (uniform bucket-level access?): {e}")

        # Attempt 2: Generate a long-lived signed URL (7 days)
        try:
            url = blob.generate_signed_url(
                expiration=timedelta(days=7),
                method="GET",
                version="v4",
            )
            logger.info(f"Using signed URL instead of public URL for blob: {blob.name}")
            return url
        except Exception as e2:
            logger.warning(f"Signed URL generation failed: {e2}")

        # Attempt 3: Return the constructed public storage URL as fallback
        # This works if the storage bucket rules allow public reads
        bucket_name = blob.bucket.name
        public_url = f"https://storage.googleapis.com/{bucket_name}/{blob.name}"
        logger.info(f"Using constructed storage URL: {public_url}")
        return public_url

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

        try:
            bucket = self._get_bucket()
            blob = bucket.blob(unique_name)
            blob.upload_from_string(content, content_type=content_type)
            url = self._make_blob_public(blob)
            logger.info(f"Uploaded leaf image: {unique_name}")
            return url
        except Exception as e:
            logger.error(f"Leaf image upload failed: {e}")
            # Return a mock local URL so the prediction can still complete
            return f"{settings.UPLOAD_TEMP_DIR}/{unique_name.replace('/', '_')}"

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
        try:
            bucket = self._get_bucket()
            blob = bucket.blob(blob_name)
            blob.upload_from_string(content, content_type="application/pdf")

            url = blob.generate_signed_url(
                expiration=timedelta(days=7),
                method="GET",
                version="v4",
            )
            logger.info(f"Uploaded report PDF: {blob_name}")
            return url
        except Exception as e:
            logger.error(f"Report PDF upload failed: {e}")
            return ""

    def upload_profile_picture(
        self,
        content: bytes,
        user_id: str,
        content_type: str = "image/jpeg",
    ) -> str:
        """Upload a user profile picture and return its public URL."""
        ext = ".jpg" if "jpeg" in content_type else ".png"
        blob_name = f"{self.PROFILE_PIC_PREFIX}{user_id}/avatar{ext}"
        try:
            bucket = self._get_bucket()
            blob = bucket.blob(blob_name)
            blob.upload_from_string(content, content_type=content_type)
            url = self._make_blob_public(blob)
            logger.info(f"Uploaded profile picture: {blob_name}")
            return url
        except Exception as e:
            logger.error(f"Profile picture upload failed: {e}")
            return ""

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
                version="v4",
            )
            return url
        except Exception as e:
            logger.error(f"Signed URL generation failed for '{blob_name}': {e}")
            return None


# Module-level singleton
storage_service = StorageService()
