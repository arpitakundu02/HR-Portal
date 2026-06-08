"""
backend/routes/leaves.py
-------------------------
Leave management endpoints.

Endpoints:
  GET  /api/leaves/balances              - Get leave balances (own or specific employee)
  POST /api/leaves/balances              - Admin: Assign/adjust leave balance
  POST /api/leaves/apply                 - Employee: Submit leave request
  GET  /api/leaves/history               - Employee: Own leave history
  GET  /api/leaves/requests              - Admin: All leave requests (filterable)
  POST /api/leaves/requests/<id>/action  - Admin: Approve or Reject a leave request
"""

from datetime import datetime
from flask import Blueprint, request, jsonify, current_app
from models import Leave, LeaveBalance, User
from extensions import db
from utils.decorators import jwt_required, admin_required
from utils.email_service import send_leave_notification

leaves_bp = Blueprint("leaves", __name__)


# ------------------------------------------------------------------
# GET /api/leaves/balances
# ------------------------------------------------------------------
@leaves_bp.route("/balances", methods=["GET"])
@jwt_required
def get_balances(current_user_id, current_user_role):
    """
    Return leave balances.
    - Employee: Own balances only.
    - Admin: Supply ?employee_id=<id> to get specific employee's balances.
    """
    if current_user_role == "Admin":
        employee_id = request.args.get("employee_id", current_user_id, type=int)
    else:
        employee_id = current_user_id  # Force own ID for employees

    balances = LeaveBalance.query.filter_by(employee_id=employee_id).all()
    return jsonify([b.to_dict() for b in balances]), 200


# ------------------------------------------------------------------
# POST /api/leaves/balances
# ------------------------------------------------------------------
@leaves_bp.route("/balances", methods=["POST"])
@admin_required
def assign_balance(current_user_id, current_user_role):
    """
    Admin-only: Assign or update annual leave balance for an employee.

    Request body:
        {
            "employee_id": 5,
            "leave_type": "APL",     // "APL" or "WFH"
            "allocated": 15
        }
    """
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body must be JSON."}), 400

    required = ["employee_id", "leave_type", "allocated"]
    for field in required:
        if data.get(field) is None:
            return jsonify({"error": f"'{field}' is required."}), 422

    employee = User.query.get(data["employee_id"])
    if not employee:
        return jsonify({"error": "Employee not found."}), 404

    leave_type = data["leave_type"]
    if leave_type not in ("APL", "WFH"):
        return jsonify({"error": "leave_type must be 'APL' or 'WFH'."}), 422

    balance = LeaveBalance.query.filter_by(
        employee_id=data["employee_id"], leave_type=leave_type
    ).first()

    if balance:
        balance.allocated = int(data["allocated"])
    else:
        balance = LeaveBalance(
            employee_id=data["employee_id"],
            leave_type=leave_type,
            allocated=int(data["allocated"]),
            used=0,
        )
        db.session.add(balance)

    balance.recalculate()
    db.session.commit()
    return jsonify(balance.to_dict()), 200


# ------------------------------------------------------------------
# POST /api/leaves/apply
# ------------------------------------------------------------------
@leaves_bp.route("/apply", methods=["POST"])
@jwt_required
def apply_leave(current_user_id, current_user_role):
    """
    Employee: Submit a leave request.
    Sends email notification to admin on submission.

    Request body:
        {
            "leave_type": "APL",
            "start_date": "2025-08-01",
            "end_date": "2025-08-05",
            "reason": "Personal work"
        }
    """
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body must be JSON."}), 400

    required = ["leave_type", "start_date", "end_date"]
    for field in required:
        if not data.get(field):
            return jsonify({"error": f"'{field}' is required."}), 422

    leave_type = data["leave_type"]
    if leave_type not in ("APL", "WFH"):
        return jsonify({"error": "leave_type must be 'APL' or 'WFH'."}), 422

    try:
        start = datetime.strptime(data["start_date"], "%Y-%m-%d").date()
        end = datetime.strptime(data["end_date"], "%Y-%m-%d").date()
    except ValueError:
        return jsonify({"error": "Dates must be in YYYY-MM-DD format."}), 422

    if end < start:
        return jsonify({"error": "end_date must be on or after start_date."}), 422

    leave = Leave(
        employee_id=current_user_id,
        leave_type=leave_type,
        start_date=start,
        end_date=end,
        reason=data.get("reason", ""),
        status="Pending",
    )
    db.session.add(leave)
    db.session.commit()

    # Send email notification to admin (non-blocking; errors logged but not raised)
    employee = User.query.get(current_user_id)
    try:
        send_leave_notification(
            employee_name=employee.name,
            employee_id=employee.employee_id,
            leave_type=leave_type,
            start_date=data["start_date"],
            end_date=data["end_date"],
            reason=data.get("reason", ""),
            recipient=current_app.config["ADMIN_NOTIFY_EMAIL"]
        )
    except Exception:
        pass  # Email errors should not fail the API response

    return jsonify(leave.to_dict()), 201


# ------------------------------------------------------------------
# GET /api/leaves/history
# ------------------------------------------------------------------
@leaves_bp.route("/history", methods=["GET"])
@jwt_required
def leave_history(current_user_id, current_user_role):
    """
    Fetch leave request history.
    - Employee: Own requests only.
    - Admin: All employees, optionally filtered by ?employee_id=, ?status=, ?leave_type=
    """
    query = Leave.query

    if current_user_role == "Admin":
        if emp_id := request.args.get("employee_id", type=int):
            query = query.filter_by(employee_id=emp_id)
        if status := request.args.get("status"):
            query = query.filter_by(status=status)
        if ltype := request.args.get("leave_type"):
            query = query.filter_by(leave_type=ltype)
    else:
        query = query.filter_by(employee_id=current_user_id)

    leaves = query.order_by(Leave.created_at.desc()).all()
    return jsonify([l.to_dict() for l in leaves]), 200


# ------------------------------------------------------------------
# GET /api/leaves/requests  (Admin pending approvals)
# ------------------------------------------------------------------
@leaves_bp.route("/requests", methods=["GET"])
@admin_required
def get_pending_requests(current_user_id, current_user_role):
    """Admin-only: View all leave requests, defaulting to Pending status."""
    status = request.args.get("status", "Pending")
    query = Leave.query
    if status != "all":
        query = query.filter_by(status=status)
    leaves = query.order_by(Leave.created_at.desc()).all()
    return jsonify([l.to_dict() for l in leaves]), 200


# ------------------------------------------------------------------
# POST /api/leaves/requests/<id>/action
# ------------------------------------------------------------------
@leaves_bp.route("/requests/<int:leave_id>/action", methods=["POST"])
@admin_required
def action_leave(leave_id, current_user_id, current_user_role):
    """
    Admin-only: Approve or Reject a leave request.
    When Approved: deduct from leave balance (negative balance supported).

    Request body:
        { "status": "Approved" }   // or "Rejected"
    """
    data = request.get_json(silent=True)
    if not data or data.get("status") not in ("Approved", "Rejected"):
        return jsonify({"error": "'status' must be 'Approved' or 'Rejected'."}), 422

    leave = Leave.query.get_or_404(leave_id)

    if leave.status != "Pending":
        return jsonify({"error": f"This request is already {leave.status}."}), 409

    leave.status = data["status"]
    leave.actioned_by = current_user_id
    leave.actioned_at = datetime.utcnow()

    # If approved, deduct from balance (supports negative values)
    if data["status"] == "Approved":
        balance = LeaveBalance.query.filter_by(
            employee_id=leave.employee_id, leave_type=leave.leave_type
        ).first()
        if balance:
            balance.used += leave.days_requested
            balance.recalculate()

    db.session.commit()

    # Notify employee of decision
    employee = User.query.get(leave.employee_id)
    try:
        send_leave_notification(
            employee_name=employee.name,
            employee_id=employee.employee_id,
            leave_type=leave.leave_type,
            start_date=leave.start_date.isoformat(),
            end_date=leave.end_date.isoformat(),
            reason=leave.reason,
            recipient=employee.email,
            status=data["status"]
        )
    except Exception:
        pass

    return jsonify(leave.to_dict()), 200
