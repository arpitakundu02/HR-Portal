# backend/utils/notification_service.py
"""
Service for creating in-app notifications.
"""

from extensions import db
from models import Notification

def create_notification(user_id, title, content, notification_type, target_id=None, action_url=None):
    """
    Creates an in-app notification record for a specific user.
    """
    try:
        notification = Notification(
            user_id=user_id,
            title=title,
            content=content,
            notification_type=notification_type,
            target_id=target_id,
            action_url=action_url,
            is_read=False
        )
        db.session.add(notification)
        db.session.commit()
        return notification
    except Exception as e:
        db.session.rollback()
        # Non-blocking: log the error, return None
        print(f"[ERROR] Failed to create in-app notification: {e}")
        return None
