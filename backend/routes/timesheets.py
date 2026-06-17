# backend/routes/timesheets.py
"""
backend/routes/timesheets.py
----------------------------
Blueprint for Daily Timesheet module.
"""

from datetime import datetime, date
from flask import Blueprint, request, jsonify
from extensions import db
from models import User, Timesheet
from utils.decorators import jwt_required

timesheets_bp = Blueprint("timesheets", __name__)

@timesheets_bp.route("", methods=["POST"])
@jwt_required
def create_timesheet(current_user_id, current_user_role):
    """
    POST /api/timesheets
    Submit daily timesheet log.
    """
    data = request.get_json(silent=True) or {}
    date_str = data.get("date", "").strip()
    task_name = data.get("task_name", "").strip()
    hours_spent_val = data.get("hours_spent")
    description = data.get("description", "").strip()

    if not date_str or not task_name or hours_spent_val is None:
        return jsonify({"error": "date, task_name, and hours_spent are required."}), 422

    try:
        req_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        return jsonify({"error": "date must be in YYYY-MM-DD format."}), 422

    try:
        hours_spent = float(hours_spent_val)
        if hours_spent <= 0:
            return jsonify({"error": "hours_spent must be greater than 0."}), 400
        if hours_spent > 24:
            return jsonify({"error": "hours_spent cannot exceed 24 hours."}), 400
    except ValueError:
        return jsonify({"error": "hours_spent must be a valid number."}), 422

    try:
        timesheet = Timesheet(
            employee_id=current_user_id,
            date=req_date,
            task_name=task_name,
            hours_spent=hours_spent,
            description=description,
            status="Submitted"
        )
        db.session.add(timesheet)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to submit timesheet: {str(e)}"}), 500

    return jsonify({
        "message": "Timesheet submitted successfully.",
        "timesheet": timesheet.to_dict()
    }), 201


@timesheets_bp.route("", methods=["GET"])
@jwt_required
def get_my_timesheets(current_user_id, current_user_role):
    """
    GET /api/timesheets
    Get timesheets for the logged-in employee.
    """
    timesheets = Timesheet.query.filter_by(employee_id=current_user_id).order_by(Timesheet.date.desc(), Timesheet.created_at.desc()).all()
    return jsonify([t.to_dict() for t in timesheets]), 200


@timesheets_bp.route("/team", methods=["GET"])
@jwt_required
def get_team_timesheets(current_user_id, current_user_role):
    """
    GET /api/timesheets/team
    Retrieve timesheets of direct reports (for supervisors) or all timesheets (for Admins).
    Supports filters: employee_id and date.
    """
    if current_user_role == "Admin":
        query = Timesheet.query
    else:
        # Find direct reports
        direct_reports = User.query.filter_by(manager_id=current_user_id).all()
        if not direct_reports:
            return jsonify([]), 200
        report_ids = [u.id for u in direct_reports]
        query = Timesheet.query.filter(Timesheet.employee_id.in_(report_ids))

    # Filters
    employee_filter = request.args.get("employee_id")
    date_filter = request.args.get("date")

    if employee_filter:
        try:
            emp_id = int(employee_filter)
            if current_user_role != "Admin":
                # Ensure the user is a direct report
                is_report = User.query.filter_by(id=emp_id, manager_id=current_user_id).first() is not None
                if not is_report:
                    return jsonify({"error": "You can only view timesheets of your direct reports."}), 403
            query = query.filter(Timesheet.employee_id == emp_id)
        except ValueError:
            return jsonify({"error": "Invalid employee_id filter."}), 400

    if date_filter:
        try:
            filter_date = datetime.strptime(date_filter, "%Y-%m-%d").date()
            query = query.filter(Timesheet.date == filter_date)
        except ValueError:
            return jsonify({"error": "Invalid date filter format. Use YYYY-MM-DD."}), 400

    timesheets = query.order_by(Timesheet.date.desc(), Timesheet.created_at.desc()).all()
    return jsonify([t.to_dict() for t in timesheets]), 200
