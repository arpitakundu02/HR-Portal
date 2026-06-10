"""
backend/routes/employees.py
----------------------------
Employee management endpoints.
Admin: Full CRUD + resume upload.
Employee: View list (limited), view/edit own profile.

Endpoints:
  GET    /api/employees               - List employees (Admin: all; Employee: directory)
  POST   /api/employees               - Admin: Create new employee
  GET    /api/employees/<id>          - Get employee detail
  PUT    /api/employees/<id>          - Update employee profile
  DELETE /api/employees/<id>          - Admin: Delete employee
  POST   /api/employees/<id>/resume   - Admin: Upload employee resume
"""

import os
import bcrypt
from datetime import datetime, date
from flask import Blueprint, request, jsonify, current_app, send_from_directory
from werkzeug.utils import secure_filename
from models import User, Department, LeaveBalance
from extensions import db
from utils.decorators import jwt_required, admin_required
from utils.email_service import send_employee_notification, send_resume_notification

employees_bp = Blueprint("employees", __name__)

ALLOWED_EXTENSIONS = {"pdf", "doc", "docx"}


def _allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def _auto_employee_id() -> str:
    """Generate next sequential employee ID like HR-001."""
    last = User.query.order_by(User.id.desc()).first()
    next_num = (last.id + 1) if last else 1
    return f"HR-{next_num:03d}"


def _get_company_date():
    """Return the current date in Asia/Kolkata (IST) timezone."""
    import datetime as dt
    kolkata_tz = dt.timezone(dt.timedelta(hours=5, minutes=30))
    return dt.datetime.now(kolkata_tz).date()


def _get_availability_status(user_obj) -> str:
    """Calculate the availability status of a user for the current date."""
    from models import Leave, Attendance
    today = _get_company_date()
    approved_leave = Leave.query.filter(
        Leave.employee_id == user_obj.id,
        Leave.status == "Approved",
        Leave.start_date <= today,
        Leave.end_date >= today
    ).first()

    if approved_leave:
        if approved_leave.leave_type == "APL":
            return "On Leave"
        elif approved_leave.leave_type == "WFH":
            return "Work From Home"
    else:
        att = Attendance.query.filter_by(employee_id=user_obj.id, date=today).first()
        if att and att.check_in:
            if not att.check_out:
                return "Present"
    return "Unavailable"


def _get_upcoming_leave(user_obj):
    """Get the closest future approved leave details for the user."""
    from models import Leave
    today = _get_company_date()
    next_leave = Leave.query.filter(
        Leave.employee_id == user_obj.id,
        Leave.status == "Approved",
        Leave.start_date > today
    ).order_by(Leave.start_date.asc()).first()

    if not next_leave:
        return None

    days_until_start = (next_leave.start_date - today).days

    return {
        "leave_type": next_leave.leave_type,
        "start_date": next_leave.start_date.isoformat(),
        "end_date": next_leave.end_date.isoformat(),
        "days_until_start": days_until_start
    }



# ------------------------------------------------------------------
# GET /api/employees
# ------------------------------------------------------------------
@employees_bp.route("/", methods=["GET"])
@jwt_required
def list_employees(current_user_id, current_user_role):
    """
    List employees.
    - Admin: All employees with optional search & department filter.
    - Employee: Public directory (name, department, rank only).

    Query params:
        search      (str)  - Filter by name or employee_id
        department  (int)  - Filter by department_id
        page        (int)  - Page number (default 1)
        per_page    (int)  - Results per page (default 20)
    """
    search = request.args.get("search", "").strip()
    department_id = request.args.get("department", type=int)
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)

    query = User.query.filter_by(is_active=True)

    if search:
        like = f"%{search}%"
        query = query.filter(
            (User.name.ilike(like)) | (User.employee_id.ilike(like)) | (User.email.ilike(like))
        )
    if department_id:
        query = query.filter_by(department_id=department_id)

    pagination = query.order_by(User.name).paginate(page=page, per_page=per_page, error_out=False)

    user = User.query.get(current_user_id)
    user_dept_id = user.department_id if user else None

    query = User.query.filter_by(is_active=True)

    if current_user_role != "Admin":
        if not user_dept_id:
            # If user has no department, they see nobody
            return jsonify({
                "employees": [],
                "total": 0,
                "page": page,
                "pages": 0,
            }), 200
        query = query.filter_by(department_id=user_dept_id)

    if search:
        like = f"%{search}%"
        if current_user_role == "Admin":
            query = query.filter(
                (User.name.ilike(like)) | (User.employee_id.ilike(like)) | (User.email.ilike(like))
            )
        else:
            query = query.filter(
                (User.name.ilike(like)) | (User.email.ilike(like))
            )
    if department_id and current_user_role == "Admin":
        query = query.filter_by(department_id=department_id)

    pagination = query.order_by(User.name).paginate(page=page, per_page=per_page, error_out=False)

    employees = []
    if current_user_role == "Admin":
        for e in pagination.items:
            emp_data = e.to_dict(include_sensitive=True)
            emp_data["availability_status"] = _get_availability_status(e)
            emp_data["upcoming_leave"] = _get_upcoming_leave(e)
            employees.append(emp_data)
    else:
        for e in pagination.items:
            employees.append({
                "id": e.id,
                "name": e.name,
                "email": e.email,
                "department_id": e.department_id,
                "department_name": e.department.name if e.department else None,
                "rank": e.rank,
                "role": e.role,
                "is_active": e.is_active,
                "availability_status": _get_availability_status(e),
                "upcoming_leave": _get_upcoming_leave(e)
            })

    return jsonify({
        "employees": employees,
        "total": pagination.total,
        "page": page,
        "pages": pagination.pages,
    }), 200

# ------------------------------------------------------------------
# GET /api/employees/stats
# ------------------------------------------------------------------
@employees_bp.route("/stats", methods=["GET"])
@admin_required
def get_employee_stats(current_user_id, current_user_role):
    """
    Get aggregated employee statistics for the dashboard.
    Returns active employees count and distribution by department.
    """
    from sqlalchemy import func
    from models import Department
    
    # Count active employees
    active_count = User.query.filter_by(is_active=True).count()
    
    # Query department distribution for active employees
    # Using group_by and outer join to also count employees with no department
    results = db.session.query(
        Department.name,
        func.count(User.id)
    ).select_from(User).outerjoin(
        Department, User.department_id == Department.id
    ).filter(
        User.is_active == True
    ).group_by(
        User.department_id, Department.name
    ).all()
    
    distribution = []
    for dept_name, count in results:
        distribution.append({
            "name": dept_name if dept_name is not None else "Unassigned",
            "count": count
        })
        
    return jsonify({
        "active_employees": active_count,
        "department_distribution": distribution
    }), 200


# ------------------------------------------------------------------
# POST /api/employees
# ------------------------------------------------------------------
@employees_bp.route("/", methods=["POST"])
@admin_required
def create_employee(current_user_id, current_user_role):
    """
    Admin-only: Create a new employee account.

    Required JSON fields: name, email, password, role
    Optional: All other profile fields.
    """
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body must be JSON."}), 400

    required = ["name", "email", "password"]
    for field in required:
        if not data.get(field):
            return jsonify({"error": f"'{field}' is required."}), 422

    email = data["email"].strip().lower()
    if User.query.filter_by(email=email).first():
        return jsonify({"error": "A user with this email already exists."}), 409

    # Hash password
    pw_hash = bcrypt.hashpw(data["password"].encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    manager_id = data.get("manager_id")
    if manager_id:
        manager = User.query.get(manager_id)
        if not manager or not manager.is_active:
            return jsonify({"error": "Selected manager does not exist or is inactive."}), 422

    employee = User(
        employee_id=data.get("employee_id") or _auto_employee_id(),
        email=email,
        password_hash=pw_hash,
        role=data.get("role", "Employee"),
        name=data["name"],
        fathers_name=data.get("fathers_name"),
        dob=data.get("dob"),
        blood_group=data.get("blood_group"),
        address=data.get("address"),
        permanent_address=data.get("permanent_address"),
        current_address=data.get("current_address"),
        emergency_contact=data.get("emergency_contact"),
        department_id=data.get("department_id"),
        date_of_joining=data.get("date_of_joining"),
        salary=data.get("salary"),
        rank=data.get("rank"),
        manager_id=manager_id,
        aadhar_number=data.get("aadhar_number"),
    )
    db.session.add(employee)
    db.session.flush()  # Flush to get employee.id for leave balances

    # Initialise leave balances (APL and WFH) for the new employee
    for leave_type in ["APL", "WFH"]:
        balance = LeaveBalance(
            employee_id=employee.id,
            leave_type=leave_type,
            allocated=0,
            used=0,
            remaining=0,
        )
        db.session.add(balance)

    db.session.commit()

    # Send onboarding email
    try:
        portal_url = "http://localhost:3000"
        send_employee_notification(
            employee_id=employee.employee_id,
            email=employee.email,
            temp_password=data["password"],
            portal_url=portal_url,
            recipient=employee.email,
            employee_name=employee.name
        )
    except Exception:
        pass

    return jsonify(employee.to_dict(include_sensitive=True)), 201


# ------------------------------------------------------------------
# GET /api/employees/<id>
# ------------------------------------------------------------------
@employees_bp.route("/<int:emp_id>", methods=["GET"])
@jwt_required
def get_employee(emp_id, current_user_id, current_user_role):
    """Retrieve a single employee's profile."""
    employee = User.query.get_or_404(emp_id)

    if current_user_role != "Admin" and current_user_id != emp_id:
        # Check department matching
        user = User.query.get(current_user_id)
        if not user or user.department_id != employee.department_id or not user.department_id:
            return jsonify({"error": "Access denied."}), 403

        return jsonify({
            "id": employee.id,
            "name": employee.name,
            "email": employee.email,
            "department_id": employee.department_id,
            "department_name": employee.department.name if employee.department else None,
            "rank": employee.rank,
            "role": employee.role,
            "is_active": employee.is_active,
            "availability_status": _get_availability_status(employee),
            "upcoming_leave": _get_upcoming_leave(employee)
        }), 200

    emp_data = employee.to_dict(include_sensitive=(current_user_role == "Admin" or current_user_id == emp_id))
    emp_data["availability_status"] = _get_availability_status(employee)
    emp_data["upcoming_leave"] = _get_upcoming_leave(employee)
    return jsonify(emp_data), 200


# ------------------------------------------------------------------
# PUT /api/employees/<id>
# ------------------------------------------------------------------
@employees_bp.route("/<int:emp_id>", methods=["PUT"])
@jwt_required
def update_employee(emp_id, current_user_id, current_user_role):
    """
    Update employee profile.
    - Admin: Can update any field for any employee.
    - Employee: Can only update their own limited fields
                (address, current_address, emergency_contact).
    """
    if current_user_role != "Admin" and current_user_id != emp_id:
        return jsonify({"error": "Access denied."}), 403

    employee = User.query.get_or_404(emp_id)
    data = request.get_json(silent=True) or {}

    if current_user_role == "Admin":
        # Admin can change any field
        admin_fields = [
            "name", "fathers_name", "dob", "blood_group",
            "address", "permanent_address", "current_address", "emergency_contact",
            "department_id", "date_of_joining", "salary", "rank",
            "aadhar_number", "role", "is_active",
        ]
        for field in admin_fields:
            if field in data:
                setattr(employee, field, data[field])

        if "manager_id" in data:
            m_id = data["manager_id"]
            if m_id:
                if m_id == employee.id:
                    return jsonify({"error": "An employee cannot be their own manager."}), 422
                
                # Check for circular reporting chain
                visited = set()
                curr_id = m_id
                while curr_id:
                    if curr_id == employee.id:
                        return jsonify({"error": "Circular reporting chain detected."}), 422
                    if curr_id in visited:
                        break
                    visited.add(curr_id)
                    curr_mgr = User.query.get(curr_id)
                    curr_id = curr_mgr.manager_id if curr_mgr else None

                manager = User.query.get(m_id)
                if not manager or not manager.is_active:
                    return jsonify({"error": "Selected manager does not exist or is inactive."}), 422
            employee.manager_id = m_id

        # Allow password reset by admin
        if data.get("password"):
            employee.password_hash = bcrypt.hashpw(
                data["password"].encode("utf-8"), bcrypt.gensalt()
            ).decode("utf-8")
    else:
        # Employee self-editable fields only
        self_fields = ["address", "current_address", "emergency_contact"]
        for field in self_fields:
            if field in data:
                setattr(employee, field, data[field])

    db.session.commit()
    return jsonify(employee.to_dict(include_sensitive=True)), 200


# ------------------------------------------------------------------
# DELETE /api/employees/<id>
# ------------------------------------------------------------------
@employees_bp.route("/<int:emp_id>", methods=["DELETE"])
@admin_required
def delete_employee(emp_id, current_user_id, current_user_role):
    """Admin-only: Soft-delete an employee (sets is_active = False)."""
    from models import Department
    employee = User.query.get_or_404(emp_id)
    if employee.id == current_user_id:
        return jsonify({"error": "Admin cannot deactivate their own account."}), 400

    employee.is_active = False
    
    # Safely handle direct reports by setting their manager to NULL
    User.query.filter_by(manager_id=employee.id).update({User.manager_id: None})
    
    # Safely handle department manager references by setting them to NULL
    Department.query.filter_by(manager_id=employee.id).update({Department.manager_id: None})
    
    db.session.commit()
    return jsonify({"message": f"Employee '{employee.name}' has been deactivated."}), 200


# ------------------------------------------------------------------
# POST /api/employees/<id>/resume
# ------------------------------------------------------------------
@employees_bp.route("/<int:emp_id>/resume", methods=["POST"])
@jwt_required
def upload_resume(emp_id, current_user_id, current_user_role):
    """Upload a resume PDF/DOC for an employee."""
    employee = User.query.get_or_404(emp_id)

    if current_user_role != "Admin" and current_user_id != emp_id:
        return jsonify({"error": "Unauthorized. You can only upload your own resume."}), 403

    if "resume" not in request.files:
        return jsonify({"error": "No file part in the request."}), 400

    file = request.files["resume"]
    if file.filename == "":
        return jsonify({"error": "No file selected."}), 400

    if not _allowed_file(file.filename):
        return jsonify({"error": "File type not allowed. Use PDF, DOC, or DOCX."}), 422

    filename = secure_filename(f"resume_{emp_id}_{file.filename}")
    upload_path = current_app.config["UPLOAD_FOLDER"]
    os.makedirs(upload_path, exist_ok=True)
    file.save(os.path.join(upload_path, filename))

    # Update database record
    employee.resume_url = f"/api/employees/uploads/{filename}"
    db.session.commit()

    # Send resume upload notification to Admin and confirmation to Employee
    try:
        send_resume_notification(
            employee_name=employee.name,
            employee_id=employee.employee_id,
            upload_timestamp=datetime.utcnow().isoformat() + " UTC",
            recipient=current_app.config["ADMIN_NOTIFY_EMAIL"]
        )
        from utils.email_service import send_resume_confirmation
        send_resume_confirmation(
            employee_name=employee.name,
            employee_id=employee.employee_id,
            upload_timestamp=datetime.utcnow().isoformat() + " UTC",
            recipient=employee.email
        )
    except Exception:
        pass

    return jsonify({"message": "Resume uploaded successfully.", "resume_url": employee.resume_url}), 200


# ------------------------------------------------------------------
# GET /api/employees/uploads/<filename>  (serve uploaded files)
# ------------------------------------------------------------------
@employees_bp.route("/uploads/<path:filename>", methods=["GET"])
@jwt_required
def serve_resume(filename, current_user_id, current_user_role):
    """Serve uploaded resume files (requires authentication)."""
    if current_user_role != "Admin":
        parts = filename.split("_")
        if len(parts) >= 2 and parts[0] == "resume":
            try:
                owner_id = int(parts[1])
                if owner_id != current_user_id:
                    return jsonify({"error": "Access denied. You do not own this file."}), 403
            except ValueError:
                return jsonify({"error": "Access denied. Invalid file owner ID."}), 403
        else:
            return jsonify({"error": "Access denied. Invalid file name format."}), 403

    upload_path = current_app.config["UPLOAD_FOLDER"]
    return send_from_directory(upload_path, filename)
