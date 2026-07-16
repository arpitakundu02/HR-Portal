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

from datetime import datetime, date
import calendar
from flask import Blueprint, request, jsonify, current_app
from models import Leave, LeaveBalance, User
from extensions import db
from utils.decorators import jwt_required, admin_required
from utils.email_service import send_leave_notification

leaves_bp = Blueprint("leaves", __name__)

def get_approved_apl_days_in_year(employee_id, year):
    first_day = date(year, 1, 1)
    last_day = date(year, 12, 31)
    approved_leaves = Leave.query.filter(
        Leave.employee_id == employee_id,
        Leave.leave_type == "APL",
        Leave.status == "Approved",
        Leave.start_date >= first_day,
        Leave.start_date <= last_day
    ).all()
    return sum(l.days_requested for l in approved_leaves)

def get_approved_wfh_days_in_month(employee_id, year, month):
    first_day = date(year, month, 1)
    last_day_num = calendar.monthrange(year, month)[1]
    last_day = date(year, month, last_day_num)
    approved_leaves = Leave.query.filter(
        Leave.employee_id == employee_id,
        Leave.leave_type == "WFH",
        Leave.status == "Approved",
        Leave.start_date >= first_day,
        Leave.start_date <= last_day
    ).all()
    return sum(l.days_requested for l in approved_leaves)


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



    resp_transfer_id = data.get("responsibility_transfer_id")
    if not resp_transfer_id:
        return jsonify({"error": "'responsibility_transfer_id' is required."}), 422

    try:
        resp_transfer_id = int(resp_transfer_id)
    except (TypeError, ValueError):
        return jsonify({"error": "'responsibility_transfer_id' must be an integer."}), 422

    if resp_transfer_id == current_user_id:
        return jsonify({"error": "You cannot assign responsibility transfer to yourself."}), 422

    employee = User.query.get(current_user_id)
    transfer_owner = User.query.get(resp_transfer_id)

    if not transfer_owner or not transfer_owner.is_active:
        return jsonify({"error": "Selected responsibility owner must be an active employee."}), 422

    if not employee or employee.department_id != transfer_owner.department_id or not employee.department_id:
        return jsonify({"error": "Selected responsibility owner must belong to your department."}), 422

    leave = Leave(
        employee_id=current_user_id,
        leave_type=leave_type,
        start_date=start,
        end_date=end,
        reason=data.get("reason", ""),
        status="Pending",
        responsibility_transfer_id=resp_transfer_id,
    )
    db.session.add(leave)
    db.session.commit()

    # Trigger in-app notification to manager and delegate
    from utils.notification_service import create_notification
    try:
        if employee.manager_id:
            create_notification(
                user_id=employee.manager_id,
                title="Leave Approval Required",
                content=f"{employee.name} has applied for leave from {data['start_date']} to {data['end_date']}.",
                notification_type="Leave",
                target_id=leave.id,
                action_url="/leaves"
            )
        create_notification(
            user_id=resp_transfer_id,
            title="Responsibility Transfer Delegated",
            content=f"{employee.name} has delegated responsibilities to you from {data['start_date']} to {data['end_date']}.",
            notification_type="Leave",
            target_id=leave.id,
            action_url="/leaves"
        )
    except Exception:
        pass

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
# GET /api/leaves/stats
# ------------------------------------------------------------------
@leaves_bp.route("/stats", methods=["GET"])
@admin_required
def get_leave_stats(current_user_id, current_user_role):
    """
    Get aggregated leave statistics.
    Returns pending count and status distribution (active employees only by default).
    """
    from sqlalchemy import func
    
    include_inactive = request.args.get("include_inactive", "false").lower() == "true"
    
    query = db.session.query(
        Leave.status,
        func.count(Leave.id)
    )
    
    if not include_inactive:
        query = query.join(User, Leave.employee_id == User.id).filter(User.is_active == True)
        
    results = query.group_by(Leave.status).all()
    
    status_distribution = {
        "Pending": 0,
        "Approved": 0,
        "Rejected": 0
    }
    
    for status, count in results:
        if status in status_distribution:
            status_distribution[status] = count
            
    return jsonify({
        "pending_leaves": status_distribution["Pending"],
        "status_distribution": status_distribution
    }), 200


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
    employee = User.query.get(leave.employee_id)
    if not employee or not employee.is_active:
        return jsonify({"error": "Cannot approve or action leaves for inactive employees."}), 400

    if leave.employee_id == current_user_id:
        return jsonify({"error": "Access denied. You cannot approve your own leave request."}), 403

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

    # Notify responsibility transfer owner if approved
    if data["status"] == "Approved" and leave.responsibility_transfer_id:
        try:
            transfer_owner = User.query.get(leave.responsibility_transfer_id)
            if transfer_owner and transfer_owner.email:
                from utils.email_service import send_email_async
                subject = "Leave Responsibility Transfer Assignment"
                body = f"""
                <h3 style="color: #4f46e5; margin-top: 0;">Responsibility Transfer Assignment</h3>
                <p>Hello {transfer_owner.name},</p>
                <p>You have been assigned as the temporary responsibility owner for <strong>{employee.name}</strong> during their leave period.</p>
                <hr style="border: 0; border-top: 1px solid #e5e7eb; margin: 16px 0;">
                <table style="width: 100%; font-size: 14px; border-collapse: collapse;">
                  <tr><td style="padding: 6px 0; color: #6b7280; font-weight: 600;">Employee Name:</td><td style="padding: 6px 0; font-weight: 600;">{employee.name}</td></tr>
                  <tr><td style="padding: 6px 0; color: #6b7280; font-weight: 600;">Leave Period:</td><td style="padding: 6px 0;">{leave.start_date.isoformat()} to {leave.end_date.isoformat()}</td></tr>
                  <tr><td style="padding: 6px 0; color: #6b7280; font-weight: 600;">Transfer Type:</td><td style="padding: 6px 0;">Temporary Responsibility Owner</td></tr>
                </table>
                """
                from utils.email_service import HTML_TEMPLATE_WRAPPER
                full_body = HTML_TEMPLATE_WRAPPER.format(content=body)
                send_email_async(subject, full_body, transfer_owner.email)
        except Exception:
            pass

    return jsonify(leave.to_dict()), 200


# ------------------------------------------------------------------
# GET /api/leaves/team  (Supervisor direct reports leaves)
# ------------------------------------------------------------------
@leaves_bp.route("/team", methods=["GET"])
@jwt_required
def get_team_leaves(current_user_id, current_user_role):
    """
    Supervisor view of leaves of their direct reports.
    """
    reports = User.query.filter_by(manager_id=current_user_id, is_active=True).all()
    if not reports:
        return jsonify([]), 200
    report_ids = [r.id for r in reports]
    
    status = request.args.get("status")
    query = Leave.query.filter(Leave.employee_id.in_(report_ids))
    if status and status != "all":
        query = query.filter_by(status=status)
        
    leaves = query.order_by(Leave.created_at.desc()).all()
    return jsonify([l.to_dict() for l in leaves]), 200

