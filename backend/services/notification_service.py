"""
AgriCrop – Notification Service
Handles user notifications for disease alerts, updates, and system messages.
"""

from datetime import datetime
from typing import Optional, List
from loguru import logger

from backend.config import settings
from backend.services.firebase_service import FirestoreService
from backend.utils.helpers import generate_id, utc_now, severity_from_confidence

_notif_svc = FirestoreService(settings.COLLECTION_NOTIFICATIONS)


class NotificationService:
    """Manages user notifications."""

    def disease_alert(
        self,
        user_id: str,
        disease_name: str,
        severity: str,
        prediction_id: str,
    ) -> str:
        """
        Send a disease detection alert notification.
        """
        notif_id = generate_id("notif")
        now = utc_now()

        severity_emoji = {
            "severe": "🔴",
            "moderate": "🟠",
            "mild": "🟡",
            "healthy": "🌿",
        }

        notif_doc = {
            "notification_id": notif_id,
            "user_id": user_id,
            "type": "disease_alert",
            "title": f"{severity_emoji.get(severity, '⚠️')} Disease Detected: {disease_name}",
            "message": f"Severity: {severity}. View details and treatment options in your history.",
            "related_prediction_id": prediction_id,
            "severity": severity,
            "is_read": False,
            "created_at": now,
            "read_at": None,
        }

        _notif_svc.create(notif_id, notif_doc)
        logger.info(f"✅ Disease alert sent to {user_id}: {disease_name}")
        return notif_id

    def soil_alert(
        self,
        user_id: str,
        moisture_percent: float,
        prediction_id: str,
    ) -> str:
        """
        Send a soil moisture alert notification.
        """
        notif_id = generate_id("notif")
        now = utc_now()

        if moisture_percent < 20:
            title = "💧 Urgent: Soil Critically Dry"
            message = "Immediate irrigation needed. Soil moisture is critically low."
        elif moisture_percent < 40:
            title = "💧 Warning: Low Soil Moisture"
            message = "Consider watering your crops soon."
        else:
            title = "💧 Soil Moisture Update"
            message = f"Current soil moisture: {moisture_percent:.1f}%"

        notif_doc = {
            "notification_id": notif_id,
            "user_id": user_id,
            "type": "soil_alert",
            "title": title,
            "message": message,
            "related_prediction_id": prediction_id,
            "moisture_percent": moisture_percent,
            "is_read": False,
            "created_at": now,
            "read_at": None,
        }

        _notif_svc.create(notif_id, notif_doc)
        logger.info(f"✅ Soil alert sent to {user_id}: {moisture_percent:.1f}%")
        return notif_id

    def system_notification(
        self,
        user_id: str,
        title: str,
        message: str,
    ) -> str:
        """
        Send a system notification (welcome, updates, etc.).
        """
        notif_id = generate_id("notif")
        now = utc_now()

        notif_doc = {
            "notification_id": notif_id,
            "user_id": user_id,
            "type": "system",
            "title": title,
            "message": message,
            "is_read": False,
            "created_at": now,
            "read_at": None,
        }

        _notif_svc.create(notif_id, notif_doc)
        logger.info(f"✅ System notification sent to {user_id}: {title}")
        return notif_id

    def report_ready(
        self,
        user_id: str,
        report_id: str,
        report_type: str,
    ) -> str:
        """
        Send a notification when a report is generated.
        """
        notif_id = generate_id("notif")
        now = utc_now()

        notif_doc = {
            "notification_id": notif_id,
            "user_id": user_id,
            "type": "report_ready",
            "title": "📄 Report Ready",
            "message": f"Your {report_type} report has been generated and is ready for download.",
            "related_id": report_id,
            "is_read": False,
            "created_at": now,
            "read_at": None,
        }

        _notif_svc.create(notif_id, notif_doc)
        logger.info(f"✅ Report notification sent to {user_id}: {report_id}")
        return notif_id

    def get_notifications(
        self,
        user_id: str,
        unread_only: bool = False,
        limit: int = 50,
    ) -> List[dict]:
        """
        Get user notifications.
        """
        try:
            if unread_only:
                notifs = _notif_svc.query(
                    "user_id", "==", user_id,
                    order_by="created_at",
                    descending=True,
                    limit=limit,
                )
                notifs = [n for n in notifs if not n.get("is_read")]
            else:
                notifs = _notif_svc.query(
                    "user_id", "==", user_id,
                    order_by="created_at",
                    descending=True,
                    limit=limit,
                )
            return notifs
        except Exception as e:
            logger.error(f"Failed to get notifications for {user_id}: {e}")
            return []

    def get_unread_count(self, user_id: str) -> int:
        """
        Get count of unread notifications.
        """
        try:
            notifs = _notif_svc.query(
                "user_id", "==", user_id,
                limit=1000,
            )
            return sum(1 for n in notifs if not n.get("is_read"))
        except Exception as e:
            logger.error(f"Failed to get unread count for {user_id}: {e}")
            return 0

    def mark_as_read(self, notification_id: str) -> bool:
        """
        Mark a notification as read.
        """
        try:
            _notif_svc.update(notification_id, {
                "is_read": True,
                "read_at": utc_now(),
            })
            logger.info(f"✅ Notification marked as read: {notification_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to mark notification as read: {e}")
            return False

    def mark_all_as_read(self, user_id: str) -> bool:
        """
        Mark all user notifications as read.
        """
        try:
            notifs = _notif_svc.query(
                "user_id", "==", user_id,
                limit=1000,
            )
            for notif in notifs:
                if not notif.get("is_read"):
                    _notif_svc.update(notif["id"], {
                        "is_read": True,
                        "read_at": utc_now(),
                    })
            logger.info(f"✅ All notifications marked as read for {user_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to mark all notifications as read: {e}")
            return False


# Singleton instance
notification_service = NotificationService()
