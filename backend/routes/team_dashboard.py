# backend/routes/team_dashboard.py
"""
backend/routes/team_dashboard.py
--------------------------------
Blueprint for Supervisor's Team Dashboard.
"""

from datetime import datetime, date
import datetime as dt
from flask import Blueprint, jsonify
from extensions import db
from models import User, Attendance, Leave, Task, Timesheet, Meeting, ApprovalRequest
from utils.decorators import jwt_required

team_dashboard_bp = Blueprint("team_dashboard", __name__)

def _get_company_date() -> date:
    """Return the current date in Asia/Kolkata (IST) timezone."""
    kolkata_tz = dt.timezone(dt.timedelta(hours=5, minutes=30))
    return dt.datetime.now(kolkata_tz).date()

@team_dashboard_bp.route("/metadata", methods=["GET"])
@jwt_required
def get_team_metadata(current_user_id, current_user_role):
    """
    GET /api/team-dashboard/metadata
    Detect if the user is a supervisor (has active direct reports or is a designated Line Manager).
    """
    user = User.query.get(current_user_id)
    is_lm = getattr(user, 'is_line_manager', False) if user else False
    reports_count = User.query.filter_by(manager_id=current_user_id, is_active=True).count()
    return jsonify({
        "is_supervisor": (reports_count > 0) or is_lm,
        "reports_count": reports_count
    }), 200

@team_dashboard_bp.route("/stats", methods=["GET"])
@jwt_required
def get_team_stats(current_user_id, current_user_role):
    """
    GET /api/team-dashboard/stats
    Query and return statistics scoped only to direct reports.
    """
    reports = User.query.filter_by(manager_id=current_user_id, is_active=True).all()
    if not reports:
        return jsonify({
            "present_today": 0,
            "on_leave_today": 0,
            "absent_today": 0,
            "pending_approvals": 0,
            "pending_tasks": 0,
            "completed_tasks": 0,
            "recent_timesheets": [],
            "upcoming_meetings": []
        }), 200

    report_ids = [r.id for r in reports]
    today = _get_company_date()

    # 1. Team Attendance Stats
    present_records = Attendance.query.filter(
        Attendance.employee_id.in_(report_ids),
        Attendance.date == today,
        Attendance.check_in != None
    ).all()
    present_today = sum(1 for r in present_records if r.get_status() in ("Present", "Half Day"))

    on_leave_today = Leave.query.filter(
        Leave.employee_id.in_(report_ids),
        Leave.status == "Approved",
        Leave.start_date <= today,
        Leave.end_date >= today
    ).count()

    absent_today = max(0, len(report_ids) - present_today - on_leave_today)

    # 2. Pending Approvals assigned to current user
    pending_approvals = ApprovalRequest.query.filter_by(
        approver_id=current_user_id,
        status="Pending"
    ).count()

    # 3. Tasks Stats
    pending_tasks = Task.query.filter(
        Task.employee_id.in_(report_ids),
        Task.status.in_(["Pending", "In Progress"])
    ).count()

    completed_tasks = Task.query.filter(
        Task.employee_id.in_(report_ids),
        Task.status == "Completed"
    ).count()

    # 4. Recent Timesheets
    recent_ts = Timesheet.query.filter(
        Timesheet.employee_id.in_(report_ids)
    ).order_by(Timesheet.date.desc(), Timesheet.created_at.desc()).limit(5).all()

    # 5. Upcoming Meetings
    # Meetings scheduled in the future created by reports or manager, or for departments reports are in
    now_utc = datetime.utcnow()
    dept_ids = list(set(r.department_id for r in reports if r.department_id))
    
    meeting_filter = (
        (Meeting.created_by.in_(report_ids + [current_user_id])) |
        (Meeting.department_id.in_(dept_ids) if dept_ids else False)
    )
    
    upcoming_mtgs = Meeting.query.filter(
        Meeting.scheduled_at >= now_utc,
        meeting_filter
    ).order_by(Meeting.scheduled_at.asc()).limit(5).all()

    return jsonify({
        "present_today": present_today,
        "on_leave_today": on_leave_today,
        "absent_today": absent_today,
        "pending_approvals": pending_approvals,
        "pending_tasks": pending_tasks,
        "completed_tasks": completed_tasks,
        "recent_timesheets": [t.to_dict() for t in recent_ts],
        "upcoming_meetings": [m.to_dict() for m in upcoming_mtgs]
    }), 200
