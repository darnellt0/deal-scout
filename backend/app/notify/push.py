"""Push notification service using Firebase Cloud Messaging."""

import json
import logging
from typing import Dict, List, Optional

import httpx

from app.config import get_settings
from app.core.db import get_session
from app.core.models import User

logger = logging.getLogger(__name__)


class PushNotificationService:
    """Firebase Cloud Messaging (FCM) push notification service."""

    def __init__(self):
        """Initialize push notification service."""
        self.settings = get_settings()
        self.fcm_api_key = self.settings.openai_api_key  # Placeholder - use actual FCM key
        self.fcm_base_url = "https://fcm.googleapis.com/fcm/send"

    def send_notification(
        self,
        device_token: str,
        title: str,
        message: str,
        data: Optional[Dict] = None,
    ) -> bool:
        """
        Send a push notification to a device.

        Args:
            device_token: FCM device token
            title: Notification title
            message: Notification body message
            data: Optional custom data payload

        Returns:
            True if notification sent successfully
        """
        if not self.fcm_api_key:
            logger.warning("FCM API key not configured, skipping push notification")
            return False

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"key={self.fcm_api_key}",
        }

        payload = {
            "to": device_token,
            "notification": {
                "title": title,
                "body": message,
                "sound": "default",
                "badge": 1,
            },
        }

        if data:
            payload["data"] = data

        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.post(
                    self.fcm_base_url,
                    json=payload,
                    headers=headers,
                )
                response.raise_for_status()

            logger.info(f"Push notification sent to device {device_token}")
            return True

        except Exception as e:
            logger.error(f"Failed to send push notification: {str(e)}")
            return False

    def send_bulk_notifications(
        self,
        device_tokens: List[str],
        title: str,
        message: str,
        data: Optional[Dict] = None,
    ) -> dict:
        """
        Send push notifications to multiple devices.

        Args:
            device_tokens: List of FCM device tokens
            title: Notification title
            message: Notification body message
            data: Optional custom data payload

        Returns:
            Dictionary with success/failure counts
        """
        results = {"success": 0, "failed": 0}

        for token in device_tokens:
            if self.send_notification(token, title, message, data):
                results["success"] += 1
            else:
                results["failed"] += 1

        return results

    def send_deal_alert_notification(
        self,
        device_token: str,
        deal_title: str,
        deal_price: float,
        deal_id: int,
    ) -> bool:
        """
        Send a deal alert push notification.

        Args:
            device_token: FCM device token
            deal_title: Title of the deal
            deal_price: Price of the item
            deal_id: Listing ID for deep linking

        Returns:
            True if notification sent successfully
        """
        title = "New Deal Found!"
        message = f"{deal_title} - ${deal_price}"
        data = {
            "type": "deal_alert",
            "listing_id": str(deal_id),
            "action": "open_deal",
        }

        return self.send_notification(device_token, title, message, data)

    def send_order_notification(
        self,
        device_token: str,
        order_id: str,
        status: str,
    ) -> bool:
        """
        Send an order status notification.

        Args:
            device_token: FCM device token
            order_id: Order ID
            status: Order status (e.g., "completed", "shipped")

        Returns:
            True if notification sent successfully
        """
        status_messages = {
            "pending": "Your order is being prepared",
            "processing": "Your order is being processed",
            "shipped": "Your order has been shipped!",
            "delivered": "Your order has been delivered!",
            "cancelled": "Your order has been cancelled",
        }

        message = status_messages.get(status, f"Order status: {status}")
        title = "Order Update"
        data = {
            "type": "order_notification",
            "order_id": order_id,
            "status": status,
        }

        return self.send_notification(device_token, title, message, data)


class DeviceTokenManager:
    """Manage user device tokens for push notifications."""

    @staticmethod
    def add_device_token(
        user_id: int,
        device_token: str,
        device_type: str = "mobile",
    ) -> bool:
        """
        Store a device token for a user.

        Args:
            user_id: User ID
            device_token: FCM device token
            device_type: Device type (mobile, web, etc.)

        Returns:
            True if token stored successfully
        """
        try:
            with get_session() as session:
                user = session.query(User).filter(User.id == user_id).first()
                if not user:
                    logger.warning(f"User {user_id} not found")
                    return False

                # Store device token in user profile JSON
                if not user.profile:
                    user.profile = {}

                if "device_tokens" not in user.profile:
                    user.profile["device_tokens"] = []

                token_entry = {
                    "token": device_token,
                    "type": device_type,
                    "created_at": str(__import__("datetime").datetime.utcnow()),
                }

                # Avoid duplicates
                if device_token not in [t["token"] for t in user.profile["device_tokens"]]:
                    user.profile["device_tokens"].append(token_entry)
                    session.commit()
                    logger.info(f"Device token added for user {user_id}")
                    return True

            return True

        except Exception as e:
            logger.error(f"Failed to add device token: {str(e)}")
            return False

    @staticmethod
    def remove_device_token(user_id: int, device_token: str) -> bool:
        """
        Remove a device token for a user.

        Args:
            user_id: User ID
            device_token: FCM device token

        Returns:
            True if token removed successfully
        """
        try:
            with get_session() as session:
                user = session.query(User).filter(User.id == user_id).first()
                if not user or not user.profile:
                    return False

                if "device_tokens" in user.profile:
                    user.profile["device_tokens"] = [
                        t for t in user.profile["device_tokens"]
                        if t["token"] != device_token
                    ]
                    session.commit()
                    logger.info(f"Device token removed for user {user_id}")
                    return True

            return False

        except Exception as e:
            logger.error(f"Failed to remove device token: {str(e)}")
            return False

    @staticmethod
    def get_user_device_tokens(user_id: int) -> List[str]:
        """
        Get all device tokens for a user.

        Args:
            user_id: User ID

        Returns:
            List of device tokens
        """
        try:
            with get_session() as session:
                user = session.query(User).filter(User.id == user_id).first()
                if not user or not user.profile:
                    return []

                tokens = [
                    t["token"] for t in user.profile.get("device_tokens", [])
                    if "token" in t
                ]
                return tokens

        except Exception as e:
            logger.error(f"Failed to get device tokens: {str(e)}")
            return []


# Global push notification service instance
_push_service: Optional[PushNotificationService] = None


def get_push_service() -> PushNotificationService:
    """Get or create push notification service instance."""
    global _push_service
    if _push_service is None:
        _push_service = PushNotificationService()
    return _push_service
