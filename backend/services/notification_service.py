"""
AgriCrop – Notification Service
Creates and manages in-app notifications stored in Firestore.
Supports disease alerts, soil alerts, system messages, and report-ready events.
"""

from datetime import datetime, timezone
from typing import List, Optional
from loguru import logger

from backend.config import settings
from backend.services.firebase_service import FirestoreService
from backend.utils.helpers import generate_id, utc_now

# Firestore collection service for notifications
_notif_service = FirestoreService(settings.COLLECTION_NOTIFICATIONS)


class NotificationService:
    """
    Creates and retrieves push/in-app notifications stored in Firestore.
    Each notification is a Firestore document under the 'notifications' collection.
    """

    def create_notification(
        self,
        user_id: str,
        title: str,
        message: str,
        notif_type: str,
        related_id: Optional[str] = None,
    ) -> dict:
        """
        Create a new notification for a user.
        notif_type: 'disease_alert' | 'soil_alert' | 'system' | 'report_ready'
        """
        notif_id = generate_id("notif")
        doc = {
            "notification_id": notif_id,
            "user_id": user_id,
            "title": title,
            "message": message,
            "type": notif_type,
            "is_read": False,
            "related_id": related_id,
            "created_at": utc_now(),
        }
        _notif_service.create(notif_id, doc)
        logger.info(f"Notification created for user {user_id}: {title}")
        return doc

    def disease_alert(self, user_id: str, disease_name: str, severity: str, prediction_id: str) -> dict:
        """Notify user about a detected plant disease."""
        severity_emoji = {"healthy": "✅", "mild": "⚠️", "moderate": "🔶", "severe": "🔴"}.get(severity, "⚠️")
        return self.create_notification(
            user_id=user_id,
            title=f"{severity_emoji} Disease Detected: {disease_name}",
            message=(
                f"Your crop scan detected {disease_name} with {severity} severity. "
                "Check the diagnosis report for treatment recommendations."
            ),
            notif_type="disease_alert",
            related_id=prediction_id,
        )

    def soil_alert(self, user_id: str, moisture: float, irrigation: bool, prediction_id: str) -> dict:
        """Notify user about soil moisture prediction result."""
        if irrigation:
            title = "💧 Irrigation Recommended"
            message = f"Predicted soil moisture is {moisture:.1f}%. Irrigation is recommended today."
        else:
            title = "🌱 Soil Moisture Adequate"
            message = f"Predicted soil moisture is {moisture:.1f}%. No irrigation needed at this time."
        return self.create_notification(
            user_id=user_id,
            title=title,
            message=message,
            notif_type="soil_alert",
            related_id=prediction_id,
        )

    def report_ready(self, user_id: str, report_id: str, report_type: str) -> dict:
        """Notify user that their generated report is ready."""
        return self.create_notification(
            user_id=user_id,
            title="📄 Report Ready",
            message=f"Your {report_type} report has been generated and is ready to download.",
            notif_type="report_ready",
            related_id=report_id,
        )

    def system_notification(self, user_id: str, title: str, message: str) -> dict:
        """General system notification."""
        return self.create_notification(
            user_id=user_id,
            title=title,
            message=message,
            notif_type="system",
        )

    def get_user_notifications(
        self, user_id: str, limit: int = 50, unread_only: bool = False
    ) -> List[dict]:
        """Fetch notifications for a user, newest first."""
        docs = _notif_service.query(
            field="user_id", op="==", value=user_id,
            order_by="created_at", descending=True, limit=limit,
        )
        if unread_only:
            docs = [d for d in docs if not d.get("is_read", False)]
        return docs

    def mark_as_read(self, notification_id: str, user_id: str) -> bool:
        """Mark a single notification as read (verifies ownership)."""
        doc = _notif_service.get(notification_id)
        if not doc or doc.get("user_id") != user_id:
            return False
        _notif_service.update(notification_id, {"is_read": True})
        return True

    def mark_all_read(self, user_id: str) -> int:
        """Mark all unread notifications for a user as read. Returns count updated."""
        docs = self.get_user_notifications(user_id, unread_only=True)
        for doc in docs:
            _notif_service.update(doc["notification_id"], {"is_read": True})
        return len(docs)

    def get_unread_count(self, user_id: str) -> int:
        """Return count of unread notifications for a user."""
        docs = _notif_service.query(field="user_id", op="==", value=user_id, limit=200)
        return sum(1 for d in docs if not d.get("is_read", False))


# Module-level singleton
notification_service = NotificationService()
