"""
backend/routes/meetings.py
---------------------------
Meeting scheduling and retrieval.

Endpoints:
  GET  /api/meetings        - List meetings visible to the current user
  POST /api/meetings        - Admin: Schedule a new meeting
  PUT  /api/meetings/<id>   - Admin: Update a meeting
  DELETE /api/meetings/<id> - Admin: Cancel/delete a meeting
"""

from datetime import datetime
from flask import Blueprint, request, jsonify
from models import Meeting, User
from extensions import db
from utils.decorators import jwt_required, admin_required
from utils.email_service import send_meeting_notification

meetings_bp = Blueprint("meetings", __name__)


# ------------------------------------------------------------------
# GET /api/meetings
# ------------------------------------------------------------------
@meetings_bp.route("/", methods=["GET"])
@jwt_required
def list_meetings(current_user_id, current_user_role):
    """
    Return meetings visible to the current user.
    - Admin: All meetings.
    - Employee: Company-wide meetings (dept=NULL) + their department's meetings.

    Query params:
        upcoming (bool) - If 'true', return only future meetings.
    """
    upcoming_only = request.args.get("upcoming", "false").lower() == "true"

    if current_user_role == "Admin":
        query = Meeting.query
    else:
        # Find the employee's department
        user = User.query.get(current_user_id)
        dept_id = user.department_id if user else None

        # Show company-wide (dept_id=NULL) and own department's meetings
        query = Meeting.query.filter(
            (Meeting.department_id == None) | (Meeting.department_id == dept_id)
        )

    if upcoming_only:
        query = query.filter(Meeting.scheduled_at >= datetime.utcnow())

    meetings = query.order_by(Meeting.scheduled_at.asc()).all()
    return jsonify([m.to_dict() for m in meetings]), 200


# ------------------------------------------------------------------
# POST /api/meetings
# ------------------------------------------------------------------
@meetings_bp.route("/", methods=["POST"])
@admin_required
def create_meeting(current_user_id, current_user_role):
    """
    Admin-only: Schedule a new meeting.

    Request body:
        {
            "title": "Sprint Planning",
            "description": "Q3 sprint kick-off",
            "department_id": 2,          // null for company-wide
            "scheduled_at": "2025-08-15T10:00:00",
            "duration_minutes": 60,
            "link": "https://meet.google.com/abc-def-ghi"
        }
    """
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body must be JSON."}), 400

    if not data.get("title") or not data.get("scheduled_at"):
        return jsonify({"error": "'title' and 'scheduled_at' are required."}), 422

    try:
        scheduled_at = datetime.fromisoformat(data["scheduled_at"])
    except ValueError:
        return jsonify({"error": "'scheduled_at' must be ISO 8601 format (YYYY-MM-DDTHH:MM:SS)."}), 422

    meeting = Meeting(
        title=data["title"].strip(),
        description=data.get("description"),
        department_id=data.get("department_id"),  # None = company-wide
        scheduled_at=scheduled_at,
        duration_minutes=data.get("duration_minutes", 30),
        link=data.get("link"),
        created_by=current_user_id,
    )
    db.session.add(meeting)
    db.session.commit()

    # Query affected employees & notify Admin
    try:
        if meeting.department_id is None:
            employees = User.query.filter_by(is_active=True).all()
        else:
            employees = User.query.filter_by(department_id=meeting.department_id, is_active=True).all()
        
        recipients = [emp.email for emp in employees if emp.email]
        from flask import current_app
        admin_email = current_app.config.get("ADMIN_NOTIFY_EMAIL")
        if admin_email and admin_email not in recipients:
            recipients.append(admin_email)

        dept_name = meeting.department.name if meeting.department else "Company-Wide"
        date_str = meeting.scheduled_at.strftime("%Y-%m-%d")
        time_str = meeting.scheduled_at.strftime("%I:%M %p UTC")

        send_meeting_notification(
            meeting_title=meeting.title,
            date_str=date_str,
            time_str=time_str,
            department_name=dept_name,
            description=meeting.description,
            recipients=recipients
        )
    except Exception:
        pass

    return jsonify(meeting.to_dict()), 201


# ------------------------------------------------------------------
# PUT /api/meetings/<id>
# ------------------------------------------------------------------
@meetings_bp.route("/<int:meeting_id>", methods=["PUT"])
@admin_required
def update_meeting(meeting_id, current_user_id, current_user_role):
    """Admin-only: Update meeting details."""
    meeting = Meeting.query.get_or_404(meeting_id)
    data = request.get_json(silent=True) or {}

    if "title" in data:
        meeting.title = data["title"].strip()
    if "description" in data:
        meeting.description = data["description"]
    if "department_id" in data:
        meeting.department_id = data["department_id"]
    if "scheduled_at" in data:
        try:
            meeting.scheduled_at = datetime.fromisoformat(data["scheduled_at"])
        except ValueError:
            return jsonify({"error": "'scheduled_at' must be ISO 8601 format."}), 422
    if "duration_minutes" in data:
        meeting.duration_minutes = data["duration_minutes"]
    if "link" in data:
        meeting.link = data["link"]

    db.session.commit()
    return jsonify(meeting.to_dict()), 200


# ------------------------------------------------------------------
# DELETE /api/meetings/<id>
# ------------------------------------------------------------------
@meetings_bp.route("/<int:meeting_id>", methods=["DELETE"])
@admin_required
def delete_meeting(meeting_id, current_user_id, current_user_role):
    """Admin-only: Delete/cancel a meeting."""
    meeting = Meeting.query.get_or_404(meeting_id)
    db.session.delete(meeting)
    db.session.commit()
    return jsonify({"message": f"Meeting '{meeting.title}' has been cancelled."}), 200
