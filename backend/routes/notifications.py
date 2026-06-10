# backend/routes/notifications.py
"""
backend/routes/notifications.py
-------------------------------
Endpoints for managing in-app notifications.
"""

from flask import Blueprint, request, jsonify
from extensions import db
from models import Notification
from utils.decorators import jwt_required

notifications_bp = Blueprint("notifications", __name__)

@notifications_bp.route("/", methods=["GET"])
@jwt_required
def get_notifications(current_user_id, current_user_role):
    """
    Get paginated notifications for the logged-in user.
    Query parameters:
        page: Page number (default: 1)
        per_page: Notifications per page (default: 20)
    """
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    
    pagination = Notification.query.filter_by(
        user_id=current_user_id
    ).order_by(
        Notification.created_at.desc()
    ).paginate(page=page, per_page=per_page, error_out=False)
    
    return jsonify({
        "notifications": [n.to_dict() for n in pagination.items],
        "total": pagination.total,
        "page": pagination.page,
        "pages": pagination.pages,
    }), 200

@notifications_bp.route("/unread-count", methods=["GET"])
@jwt_required
def get_unread_count(current_user_id, current_user_role):
    """
    Get the count of unread notifications for the logged-in user.
    """
    count = Notification.query.filter_by(
        user_id=current_user_id,
        is_read=False
    ).count()
    
    return jsonify({"unread_count": count}), 200

@notifications_bp.route("/<int:notification_id>/read", methods=["POST"])
@jwt_required
def mark_as_read(notification_id, current_user_id, current_user_role):
    """
    Mark a single notification as read.
    """
    notification = Notification.query.get_or_404(notification_id)
    
    if notification.user_id != current_user_id:
        return jsonify({"error": "Access denied. You do not own this notification."}), 403
        
    notification.is_read = True
    db.session.commit()
    
    return jsonify({"message": "Notification marked as read.", "notification": notification.to_dict()}), 200

@notifications_bp.route("/read-all", methods=["POST"])
@jwt_required
def mark_all_as_read(current_user_id, current_user_role):
    """
    Mark all notifications for the current user as read.
    """
    Notification.query.filter_by(
        user_id=current_user_id,
        is_read=False
    ).update({Notification.is_read: True})
    
    db.session.commit()
    
    return jsonify({"message": "All notifications marked as read."}), 200
