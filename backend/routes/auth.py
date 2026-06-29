"""
backend/routes/auth.py
-----------------------
Authentication endpoints:
  POST /api/auth/login    - Authenticate and return JWT
  GET  /api/auth/me       - Return current user's profile

Employees cannot self-register.
Only Admin can create employee accounts (see employees.py).
"""

import jwt
import bcrypt
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, current_app
from models import User, LeaveBalance
from extensions import db
from utils.decorators import jwt_required

auth_bp = Blueprint("auth", __name__)


# Unused _auto_employee_id helper removed



def _generate_token(user: User) -> str:
    """Generate a signed JWT for the given user."""
    payload = {
        "user_id": user.id,
        "role": user.role,
        "exp": datetime.utcnow() + timedelta(hours=current_app.config["JWT_EXP_DELTA_HOURS"]),
    }
    return jwt.encode(
        payload,
        current_app.config["JWT_SECRET_KEY"],
        algorithm=current_app.config["JWT_ALGORITHM"],
    )


# ------------------------------------------------------------------
# POST /api/auth/login
# ------------------------------------------------------------------
@auth_bp.route("/login", methods=["POST"])
def login():
    """
    Authenticate a user and return a JWT token.

    Request body:
        {
            "email": "admin@company.com",
            "password": "secret123"
        }

    Response (200):
        {
            "token": "<jwt>",
            "user": { ...profile }
        }
    """
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body must be JSON."}), 400

    email = data.get("email", "").strip().lower()
    password = data.get("password", "")
    role = data.get("role", "").strip()

    if not email or not password:
        return jsonify({"error": "Email and password are required."}), 400

    print(f"DEBUG LOGIN: email={email}, role={role}", flush=True)
    try:
        user = User.query.filter_by(email=email, is_active=True).first()
        print(f"DEBUG LOGIN: user found={user is not None}", flush=True)
        if user:
            print(f"DEBUG LOGIN: user.role={user.role}, user.is_active={user.is_active}", flush=True)
    except Exception as e:
        print(f"DEBUG LOGIN ERROR: {str(e)}", flush=True)

    user = None
    try:
        user = User.query.filter_by(email=email, is_active=True).first()
    except Exception:
        pass

    if not user:
        return jsonify({"error": "Invalid credentials."}), 401

    # Verify requested role matches user's database role
    if role and user.role != role:
        return jsonify({"error": f"Access denied. Your account does not have {role} privileges."}), 403

    # Verify password against bcrypt hash
    if not bcrypt.checkpw(password.encode("utf-8"), user.password_hash.encode("utf-8")):
        return jsonify({"error": "Invalid credentials."}), 401

    token = _generate_token(user)

    # Send login notification email to account owner
    try:
        from utils.email_service import send_login_notification
        send_login_notification(email=user.email, recipient=user.email, name=user.name)
    except Exception:
        pass

    return jsonify({
        "token": token,
        "user": user.to_dict(include_sensitive=(user.role == "Admin")),
    }), 200


# ------------------------------------------------------------------
# GET /api/auth/me
# ------------------------------------------------------------------
@auth_bp.route("/me", methods=["GET"])
@jwt_required
def get_current_user(current_user_id, current_user_role):
    """Return the authenticated user's own profile."""
    user = User.query.get(current_user_id)
    if not user:
        return jsonify({"error": "User not found."}), 404

    return jsonify(user.to_dict(include_sensitive=True)), 200


# ------------------------------------------------------------------
# GET /api/auth/badge-counts
# ------------------------------------------------------------------
@auth_bp.route("/badge-counts", methods=["GET"])
@jwt_required
def get_badge_counts(current_user_id, current_user_role):
    """
    Returns unread counts/actionable items for the logged-in user:
    - Approvals: Pending approval requests assigned/delegated to the user
    - Leaves: Pending leave requests (Admin: all company; LM: direct reports; Employee: 0)
    - Tasks: Pending or In Progress tasks assigned to the user
    - Meetings: Upcoming meetings (scheduled_at >= now) visible to the user
    - Timesheets: Submitted timesheets (Admin: all team; LM: direct reports; Employee: 0)
    - Registrations: Pending registration requests (Admin only)
    """
    from datetime import date, datetime
    from models import ApprovalRequest, WorkTransferRequest, Leave, Task, Meeting, Timesheet, RegistrationRequest
    today = date.today()
    now = datetime.utcnow()

    # 1. Approvals
    delegated_users = db.session.query(WorkTransferRequest.requester_id).filter(
        WorkTransferRequest.delegate_to_id == current_user_id,
        WorkTransferRequest.status == "Approved",
        WorkTransferRequest.start_date <= today,
        WorkTransferRequest.end_date >= today,
        WorkTransferRequest.transfer_approvals == True
    ).all()
    delegator_ids = [r[0] for r in delegated_users]
    
    app_query = ApprovalRequest.query.filter(ApprovalRequest.status == "Pending")
    if current_user_role == "Admin":
        conditions = [
            ApprovalRequest.approver_id == current_user_id,
            ApprovalRequest.module_type == "ResumeUpdate"
        ]
        if delegator_ids:
            conditions.append(ApprovalRequest.approver_id.in_(delegator_ids))
        app_query = app_query.filter(db.or_(*conditions))
    else:
        if delegator_ids:
            app_query = app_query.filter(
                db.or_(
                    ApprovalRequest.approver_id == current_user_id,
                    ApprovalRequest.approver_id.in_(delegator_ids)
                )
            )
        else:
            app_query = app_query.filter(ApprovalRequest.approver_id == current_user_id)
    approvals_count = app_query.count()

    # 2. Leaves (Pending only)
    if current_user_role == "Admin":
        leaves_count = Leave.query.filter_by(status="Pending").count()
    elif getattr(User.query.get(current_user_id), 'is_line_manager', False):
        reports = User.query.filter_by(manager_id=current_user_id, is_active=True).all()
        report_ids = [r.id for r in reports]
        if report_ids:
            leaves_count = Leave.query.filter(Leave.employee_id.in_(report_ids), Leave.status == "Pending").count()
        else:
            leaves_count = 0
    else:
        leaves_count = 0

    # 3. Tasks (Pending or In Progress assigned to user or delegated to user)
    delegated_tasks_users = db.session.query(WorkTransferRequest.requester_id).filter(
        WorkTransferRequest.delegate_to_id == current_user_id,
        WorkTransferRequest.status == "Approved",
        WorkTransferRequest.start_date <= today,
        WorkTransferRequest.end_date >= today,
        WorkTransferRequest.transfer_tasks == True
    ).all()
    delegator_task_ids = [r[0] for r in delegated_tasks_users]

    task_query = Task.query.filter(Task.status.in_(["Pending", "In Progress"]))
    if delegator_task_ids:
        task_query = task_query.filter(
            db.or_(
                Task.employee_id == current_user_id,
                Task.employee_id.in_(delegator_task_ids)
            )
        )
    else:
        task_query = task_query.filter(Task.employee_id == current_user_id)
    tasks_count = task_query.count()

    # 4. Meetings (Upcoming only, scheduled_at >= now)
    if current_user_role == "Admin":
        meetings_count = Meeting.query.filter(Meeting.scheduled_at >= now).count()
    else:
        user_obj = User.query.get(current_user_id)
        dept_id = user_obj.department_id if user_obj else None

        delegated_meetings_users = db.session.query(WorkTransferRequest.requester_id).filter(
            WorkTransferRequest.delegate_to_id == current_user_id,
            WorkTransferRequest.status == "Approved",
            WorkTransferRequest.start_date <= today,
            WorkTransferRequest.end_date >= today,
            WorkTransferRequest.transfer_meetings == True
        ).all()
        delegator_meeting_ids = [r[0] for r in delegated_meetings_users]
        delegator_dept_ids = [u.department_id for u in User.query.filter(User.id.in_(delegator_meeting_ids)).all() if u.department_id] if delegator_meeting_ids else []

        conditions = [Meeting.department_id == None]
        if dept_id:
            conditions.append(Meeting.department_id == dept_id)
        for d_id in delegator_dept_ids:
            conditions.append(Meeting.department_id == d_id)

        meetings_count = Meeting.query.filter(
            Meeting.scheduled_at >= now,
            db.or_(*conditions)
        ).count()

    # 5. Timesheets (Pending/Submitted count for supervisor review, else 0)
    if current_user_role == "Admin":
        timesheets_count = Timesheet.query.filter_by(status="Submitted").count()
    elif getattr(User.query.get(current_user_id), 'is_line_manager', False):
        reports = User.query.filter_by(manager_id=current_user_id, is_active=True).all()
        report_ids = [r.id for r in reports]
        if report_ids:
            timesheets_count = Timesheet.query.filter(Timesheet.employee_id.in_(report_ids), Timesheet.status == "Submitted").count()
        else:
            timesheets_count = 0
    else:
        timesheets_count = 0

    # 6. Registrations (Pending only, Admin-only)
    if current_user_role == "Admin":
        registrations_count = RegistrationRequest.query.filter_by(status="Pending").count()
    else:
        registrations_count = 0

    return jsonify({
        "approvals": approvals_count,
        "leaves": leaves_count,
        "tasks": tasks_count,
        "meetings": meetings_count,
        "timesheets": timesheets_count,
        "registrations": registrations_count
    }), 200

@auth_bp.route("/db-debug", methods=["GET"])
def db_debug():
    try:
        import os
        keys = [k for k in os.environ.keys() if "PASSWORD" not in k and "SECRET" not in k]
        users = User.query.all()
        user_list = [{"id": u.id, "email": u.email, "role": u.role, "is_active": u.is_active} for u in users]
        return jsonify({
            "status": "connected",
            "users_count": len(users),
            "users": user_list,
            "env_keys": keys
        }), 200
    except Exception as e:
        import os
        keys = [k for k in os.environ.keys() if "PASSWORD" not in k and "SECRET" not in k]
        db_host = os.environ.get("DB_HOST")
        db_user = os.environ.get("DB_USER")
        db_name = os.environ.get("DB_NAME")
        db_port = os.environ.get("DB_PORT")
        mysql_host = os.environ.get("MYSQLHOST")
        return jsonify({
            "status": "error",
            "error": str(e),
            "env_keys": keys,
            "db_host": db_host,
            "db_user": db_user,
            "db_name": db_name,
            "db_port": db_port,
            "mysql_host": mysql_host
        }), 500




