# backend/routes/registrations.py
"""
backend/routes/registrations.py
--------------------------------
Endpoints for employee self-registration requests and admin approvals.
"""

import bcrypt
from datetime import datetime, date
from flask import Blueprint, request, jsonify
from extensions import db
from models import RegistrationRequest, User, LeaveBalance, Department, CompOffBalance
from utils.decorators import jwt_required, admin_required

registrations_bp = Blueprint("registrations", __name__)

from utils.id_generator import generate_department_employee_id

@registrations_bp.route("/register", methods=["POST"])
def register():
    """
    Public route: Submit employee registration request.
    """
    data = request.get_json(silent=True) or {}
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")
    name = data.get("name", "").strip()

    if not email or not password or not name:
        return jsonify({"error": "Email, password, and name are required."}), 422

    # Check duplicate email in users or registration_requests
    if User.query.filter_by(email=email).first():
        return jsonify({"error": "An employee with this email already exists."}), 409

    if RegistrationRequest.query.filter_by(email=email, status="Pending").first():
        return jsonify({"error": "A registration request is already pending for this email."}), 409

    dob_str = data.get("dob")
    dob = None
    if dob_str:
        try:
            dob = datetime.strptime(dob_str, "%Y-%m-%d").date()
        except ValueError:
            return jsonify({"error": "Date of birth must be in YYYY-MM-DD format."}), 422

    pw_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    req = RegistrationRequest(
        email=email,
        password_hash=pw_hash,
        name=name,
        fathers_name=data.get("fathers_name"),
        dob=dob,
        blood_group=data.get("blood_group"),
        address=data.get("address"),
        department_id=data.get("department_id"),
        manager_id=data.get("manager_id"),
        status="Pending"
    )
    try:
        db.session.add(req)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to submit request: {str(e)}"}), 500

    return jsonify({"message": "Registration request submitted. Pending admin approval.", "request": req.to_dict()}), 201

@registrations_bp.route("/requests", methods=["GET"])
@admin_required
def list_requests(current_user_id, current_user_role):
    """
    Admin-only: List pending registration requests.
    """
    reqs = RegistrationRequest.query.order_by(RegistrationRequest.created_at.desc()).all()
    return jsonify([r.to_dict() for r in reqs]), 200

@registrations_bp.route("/requests/<int:req_id>/action", methods=["POST"])
@admin_required
def action_request(req_id, current_user_id, current_user_role):
    """
    Admin-only: Approve or Reject registration request.
    On approval: creates employee account with hashed passwords and sequential employee_id.
    On rejection: saves rejection reason.
    """
    req = RegistrationRequest.query.get_or_404(req_id)

    if req.status != "Pending":
        return jsonify({"error": "This request has already been actioned."}), 409

    data = request.get_json(silent=True) or {}
    status = data.get("status")
    reason = data.get("rejection_reason", "").strip()

    if status not in ("Approved", "Rejected"):
        return jsonify({"error": "'status' must be 'Approved' or 'Rejected'."}), 422

    if status == "Rejected" and not reason:
        return jsonify({"error": "Rejection reason is required."}), 422

    try:
        req.status = status
        req.rejection_reason = reason if status == "Rejected" else None
        req.actioned_at = datetime.utcnow()

        if status == "Approved":
            # Check duplicate email once more to prevent race condition
            if User.query.filter_by(email=req.email).first():
                return jsonify({"error": "A user with this email has been created in the meantime."}), 409

            dept_id = data.get("department_id") or req.department_id
            mgr_id = data.get("manager_id") or req.manager_id

            emp = User(
                employee_id=generate_department_employee_id(dept_id),
                email=req.email,
                password_hash=req.password_hash,
                role="Employee",
                name=req.name,
                fathers_name=req.fathers_name,
                dob=req.dob,
                blood_group=req.blood_group,
                address=req.address,
                department_id=dept_id,
                manager_id=mgr_id,
                is_active=True
            )
            db.session.add(emp)
            db.session.flush()

            # Initialize leave balances
            gender = emp.gender or "Male"
            apl_allocated = 20
            wfh_allocated = 5 if gender == "Female" else 4

            db.session.add(LeaveBalance(
                employee_id=emp.id,
                leave_type="APL",
                allocated=apl_allocated,
                used=0,
                remaining=apl_allocated,
            ))
            db.session.add(LeaveBalance(
                employee_id=emp.id,
                leave_type="WFH",
                allocated=wfh_allocated,
                used=0,
                remaining=wfh_allocated,
            ))

            # Initialize comp-off balance
            cob = CompOffBalance(
                employee_id=emp.id,
                allocated=0,
                used=0,
                remaining=0
            )
            db.session.add(cob)

        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to action request: {str(e)}"}), 500

    return jsonify({"message": f"Registration request {status.lower()} successfully.", "request": req.to_dict()}), 200
