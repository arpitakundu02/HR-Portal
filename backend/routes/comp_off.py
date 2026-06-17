# backend/routes/comp_off.py
"""
backend/routes/comp_off.py
--------------------------
Blueprint for Compensatory Off (Comp-Off) workflow.
"""

from datetime import datetime, date
from flask import Blueprint, request, jsonify
from extensions import db
from models import User, CompOffRequest, CompOffBalance, ApprovalRequest, Holiday, Attendance
from utils.decorators import jwt_required, admin_required
from utils.notification_service import create_notification
from routes.profile import determine_approver

comp_off_bp = Blueprint("comp_off", __name__)

def _get_company_date() -> date:
    """Return the current date in Asia/Kolkata (IST) timezone."""
    import datetime as dt
    kolkata_tz = dt.timezone(dt.timedelta(hours=5, minutes=30))
    return dt.datetime.now(kolkata_tz).date()

def get_or_create_comp_off_balance(employee_id, db_session=None) -> CompOffBalance:
    session = db_session or db.session
    cob = session.query(CompOffBalance).filter_by(employee_id=employee_id).first()
    if not cob:
        cob = CompOffBalance(employee_id=employee_id, allocated=0, used=0, remaining=0)
        session.add(cob)
        session.flush()
    return cob

# ------------------------------------------------------------------
# POST /api/comp-off/request
# ------------------------------------------------------------------
@comp_off_bp.route("/request", methods=["POST"])
@jwt_required
def create_comp_off_request(current_user_id, current_user_role):
    """
    Employee submits a comp-off request for a holiday/weekend date they worked.
    """
    data = request.get_json(silent=True) or {}
    date_str = data.get("date_worked", "").strip()
    reason = data.get("reason", "").strip()

    if not date_str or not reason:
        return jsonify({"error": "Date worked and reason/description are required."}), 422

    try:
        req_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        return jsonify({"error": "date_worked must be in YYYY-MM-DD format."}), 422

    today = _get_company_date()

    # 1. Prevent future dates
    if req_date >= today:
        return jsonify({"error": "Comp-Off requests cannot be submitted for today or future dates."}), 400

    # 2. Prevent requests if attendance record does not exist for that date
    attendance = Attendance.query.filter_by(employee_id=current_user_id, date=req_date).first()
    if not attendance or not attendance.check_in:
        return jsonify({"error": f"No attendance record found for {date_str}. You can only claim Comp-Off if you checked in on that day."}), 400

    # 3. Request date must be a holiday or weekend (Saturday=5, Sunday=6)
    is_weekend = req_date.weekday() in (5, 6)
    is_holiday = Holiday.query.filter_by(date=req_date).first() is not None

    if not is_weekend and not is_holiday:
        return jsonify({"error": f"The date {date_str} is neither a weekend nor a configured holiday."}), 400

    # 4. Prevent duplicate Comp-Off requests for the same date
    existing_req = CompOffRequest.query.filter_by(
        employee_id=current_user_id,
        date_worked=req_date
    ).filter(CompOffRequest.status.in_(["Pending", "Approved"])).first()

    if existing_req:
        return jsonify({"error": f"A pending or approved Comp-Off request already exists for {date_str}."}), 409

    user = User.query.get(current_user_id)
    approver_id = determine_approver(user)
    if not approver_id:
        return jsonify({"error": "No active approver (manager or admin) could be found for you."}), 500

    try:
        # Create CompOffRequest record
        comp_off = CompOffRequest(
            employee_id=current_user_id,
            date_worked=req_date,
            reason=reason,
            status="Pending"
        )
        db.session.add(comp_off)
        db.session.flush()

        # Create corresponding ApprovalRequest
        approval_req = ApprovalRequest(
            requester_id=current_user_id,
            approver_id=approver_id,
            module_type="CompOff",
            target_id=comp_off.id,
            status="Pending"
        )
        db.session.add(approval_req)
        db.session.flush()

        comp_off.approval_request_id = approval_req.id
        db.session.commit()

        # Notify approver
        create_notification(
            user_id=approver_id,
            title="New Comp-Off Request",
            content=f"{user.name} has submitted a Comp-Off request for {date_str}.",
            notification_type="CompOff",
            target_id=comp_off.id,
            action_url="/approvals"
        )

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to submit Comp-Off request: {str(e)}"}), 500

    return jsonify({
        "message": "Comp-Off request submitted successfully.",
        "request": comp_off.to_dict()
    }), 201


# ------------------------------------------------------------------
# GET /api/comp-off/history
# ------------------------------------------------------------------
@comp_off_bp.route("/history", methods=["GET"])
@jwt_required
def get_comp_off_history(current_user_id, current_user_role):
    """
    Get comp-off requests history for the logged-in employee.
    """
    reqs = CompOffRequest.query.filter_by(employee_id=current_user_id).order_by(CompOffRequest.created_at.desc()).all()
    return jsonify([r.to_dict() for r in reqs]), 200


# ------------------------------------------------------------------
# GET /api/comp-off/balance
# ------------------------------------------------------------------
@comp_off_bp.route("/balance", methods=["GET"])
@jwt_required
def get_comp_off_balance(current_user_id, current_user_role):
    """
    Get current comp-off balance for the logged-in employee.
    """
    cob = get_or_create_comp_off_balance(current_user_id)
    return jsonify(cob.to_dict()), 200


# ------------------------------------------------------------------
# GET /api/comp-off/admin/all
# ------------------------------------------------------------------
@comp_off_bp.route("/admin/all", methods=["GET"])
@admin_required
def get_admin_comp_off_all(current_user_id, current_user_role):
    """
    Admin-only: Retrieve all comp-off requests and balances.
    """
    requests_list = CompOffRequest.query.order_by(CompOffRequest.created_at.desc()).all()
    
    # Pre-populate balances for users if they don't have them
    all_users = User.query.filter_by(is_active=True).all()
    for u in all_users:
        get_or_create_comp_off_balance(u.id)
    
    balances_list = db.session.query(CompOffBalance, User).join(User, CompOffBalance.employee_id == User.id).all()
    
    serialized_balances = []
    for cob, u in balances_list:
        d = cob.to_dict()
        d["employee_name"] = u.name
        d["employee_id_code"] = u.employee_id
        d["department_name"] = u.department.name if u.department else None
        serialized_balances.append(d)

    return jsonify({
        "requests": [r.to_dict() for r in requests_list],
        "balances": serialized_balances
    }), 200
