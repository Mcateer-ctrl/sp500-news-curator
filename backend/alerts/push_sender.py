import json
import logging

from pywebpush import webpush, WebPushException

from config import settings

logger = logging.getLogger(__name__)


def send_push_notification(endpoint: str, p256dh_key: str, auth_key: str, title: str, body: str) -> bool:
    subscription_info = {
        "endpoint": endpoint,
        "keys": {
            "p256dh": p256dh_key,
            "auth": auth_key,
        },
    }

    payload = json.dumps({"title": title, "body": body})

    try:
        webpush(
            subscription_info=subscription_info,
            data=payload,
            vapid_private_key=settings.vapid_private_key,
            vapid_claims={"sub": settings.vapid_subject},
        )
        logger.info("Push notification sent: %s", title)
        return True
    except WebPushException:
        logger.exception("Failed to send push notification")
        return False
