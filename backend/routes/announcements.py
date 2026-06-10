# backend/routes/announcements.py
"""
backend/routes/announcements.py
-------------------------------
Endpoints for managing company announcements.
"""

from datetime import datetime
from flask import Blueprint, request, jsonify
from extensions import db
from models import Announcement, User, Department
from utils.decorators import jwt_required, admin_required
from utils.notification_service import create_notification

announcements_bp = Blueprint("announcements", __name__)

def is_user_manager(user):
    """Check if a user is a manager (manages at least one user or department)."""
    is_mgr = User.query.filter_by(manager_id=user.id, is_active=True).first() is not None
    if not is_mgr:
        is_mgr = Department.query.filter_by(manager_id=user.id).first() is not None
    return is_mgr

def get_applicable_announcements_query(user):
    """Return the base query for active, target-filtered announcements for a given user."""
    now = datetime.utcnow()
    query = Announcement.query.filter(
        Announcement.is_active == True,
        db.or_(Announcement.expires_at.is_(None), Announcement.expires_at >= now)
    )
    
    # Target filtering for non-admins
    if user.role != "Admin":
        conditions = [Announcement.audience_type == "All"]
        
        # Department filter
        if user.department_id:
            conditions.append(
                db.and_(
                    Announcement.audience_type == "Department",
                    Announcement.department_id == user.department_id
                )
            )
            
        # Employee role filter (non-admins)
        conditions.append(Announcement.audience_type == "Employees")
        
        # Manager filter
        if is_user_manager(user):
            conditions.append(Announcement.audience_type == "Managers")
            
        query = query.filter(db.or_(*conditions))
        
    return query

@announcements_bp.route("/", methods=["GET"])
@jwt_required
def get_announcements(current_user_id, current_user_role):
    """
    List announcements.
    - Admins: See all announcements (for management).
    - Employees/Managers: See only applicable/active/non-expired targeted announcements.
    """
    user = User.query.get_or_404(current_user_id)
    if current_user_role == "Admin":
        announcements = Announcement.query.order_by(Announcement.created_at.desc()).all()
    else:
        announcements = get_applicable_announcements_query(user).order_by(Announcement.created_at.desc()).all()
        
    return jsonify([a.to_dict() for a in announcements]), 200

@announcements_bp.route("/active", methods=["GET"])
@jwt_required
def get_active_announcements(current_user_id, current_user_role):
    """
    Get active, non-expired announcements targeted for the current user.
    """
    user = User.query.get_or_404(current_user_id)
    announcements = get_applicable_announcements_query(user).order_by(Announcement.created_at.desc()).all()
    return jsonify([a.to_dict() for a in announcements]), 200

@announcements_bp.route("/", methods=["POST"])
@admin_required
def create_announcement(current_user_id, current_user_role):
    """
    Admin-only: Create a new announcement and notify targeted users.
    """
    data = request.get_json(silent=True) or {}
    title = data.get("title", "").strip()
    content = data.get("content", "").strip()
    
    if not title or not content:
        return jsonify({"error": "title and content are required."}), 422
        
    audience_type = data.get("audience_type", "All")
    if audience_type not in ("All", "Department", "Employees", "Managers"):
        return jsonify({"error": "Invalid audience_type."}), 422
        
    department_id = data.get("department_id")
    if audience_type == "Department" and not department_id:
        return jsonify({"error": "department_id is required when audience_type is 'Department'."}), 422
        
    expires_at_str = data.get("expires_at")
    expires_at = None
    if expires_at_str:
        try:
            expires_at = datetime.fromisoformat(expires_at_str.replace("Z", ""))
        except ValueError:
            return jsonify({"error": "Invalid expires_at format. Must be ISO8601."}), 422
            
    try:
        announcement = Announcement(
            title=title,
            content=content,
            audience_type=audience_type,
            department_id=department_id,
            created_by=current_user_id,
            expires_at=expires_at,
            is_active=data.get("is_active", True)
        )
        db.session.add(announcement)
        db.session.commit()
        
        # Notification generation
        # Find active users targeted by this announcement
        target_users = []
        if audience_type == "All":
            target_users = User.query.filter_by(is_active=True).all()
        elif audience_type == "Department":
            target_users = User.query.filter_by(department_id=department_id, is_active=True).all()
        elif audience_type == "Employees":
            target_users = User.query.filter(User.is_active == True, User.role != "Admin").all()
        elif audience_type == "Managers":
            # Users who are active and direct managers of someone or managers of departments
            active_users = User.query.filter_by(is_active=True).all()
            target_users = [u for u in active_users if is_user_manager(u)]
            
        # Send notifications
        for u in target_users:
            # Avoid notifying creator
            if u.id != current_user_id:
                create_notification(
                    user_id=u.id,
                    title=f"New Announcement: {title}",
                    content=content[:100] + ("..." if len(content) > 100 else ""),
                    notification_type="Announcement",
                    target_id=announcement.id,
                    action_url="/announcements"
                )
                
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to create announcement: {str(e)}"}), 500
        
    return jsonify(announcement.to_dict()), 201

@announcements_bp.route("/<int:announcement_id>", methods=["PUT"])
@admin_required
def update_announcement(announcement_id, current_user_id, current_user_role):
    """
    Admin-only: Update an announcement.
    """
    announcement = Announcement.query.get_or_404(announcement_id)
    data = request.get_json(silent=True) or {}
    
    if "title" in data:
        announcement.title = data["title"].strip()
    if "content" in data:
        announcement.content = data["content"].strip()
    if "audience_type" in data:
        aud = data["audience_type"]
        if aud not in ("All", "Department", "Employees", "Managers"):
            return jsonify({"error": "Invalid audience_type."}), 422
        announcement.audience_type = aud
    if "department_id" in data:
        announcement.department_id = data["department_id"]
    if "expires_at" in data:
        exp_str = data["expires_at"]
        if exp_str:
            try:
                announcement.expires_at = datetime.fromisoformat(exp_str.replace("Z", ""))
            except ValueError:
                return jsonify({"error": "Invalid expires_at format."}), 422
        else:
            announcement.expires_at = None
    if "is_active" in data:
        announcement.is_active = data["is_active"]
        
    db.session.commit()
    return jsonify(announcement.to_dict()), 200

@announcements_bp.route("/<int:announcement_id>", methods=["DELETE"])
@admin_required
def delete_announcement(announcement_id, current_user_id, current_user_role):
    """
    Admin-only: Delete an announcement.
    """
    announcement = Announcement.query.get_or_404(announcement_id)
    db.session.delete(announcement)
    db.session.commit()
    return jsonify({"message": "Announcement deleted successfully."}), 200
