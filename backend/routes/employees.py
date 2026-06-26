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
from models import User, Department, LeaveBalance, CompOffBalance
from extensions import db
from utils.decorators import jwt_required, admin_required
from utils.email_service import send_employee_notification, send_resume_notification

employees_bp = Blueprint("employees", __name__)

ALLOWED_EXTENSIONS = {"pdf", "doc", "docx"}


def _allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


from utils.id_generator import generate_department_employee_id


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
            return "Active / Present"
    return "Absent"


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

    user = User.query.get(current_user_id)
    is_lm = getattr(user, 'is_line_manager', False) if user else False
    user_dept_id = user.department_id if user else None

    query = User.query.filter_by(is_active=True)

    if current_user_role != "Admin":
        if is_lm:
            from models import Department
            managed_depts = Department.query.filter_by(manager_id=current_user_id).all()
            managed_dept_ids = [d.id for d in managed_depts]
            
            conds = [
                (User.role == "Admin"),
                (User.is_line_manager == True),
                (User.manager_id == current_user_id),
                (User.id == current_user_id)
            ]
            if user_dept_id is not None:
                conds.append(User.department_id == user_dept_id)
            if managed_dept_ids:
                conds.append(User.department_id.in_(managed_dept_ids))
                
            final_cond = conds[0]
            for cond in conds[1:]:
                final_cond = final_cond | cond
                
            query = query.filter(final_cond)
        else:
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
        if current_user_role == "Admin" or is_lm:
            query = query.filter(
                (User.name.ilike(like)) | (User.employee_id.ilike(like)) | (User.email.ilike(like)) | (User.phone_number.ilike(like))
            )
        else:
            query = query.filter(
                (User.name.ilike(like)) | (User.email.ilike(like)) | (User.phone_number.ilike(like))
            )
    if department_id and (current_user_role == "Admin" or is_lm):
        query = query.filter_by(department_id=department_id)

    pagination = query.order_by(User.name).paginate(page=page, per_page=per_page, error_out=False)

    employees = []
    if current_user_role == "Admin" or is_lm:
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
                "is_line_manager": e.is_line_manager,
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
# GET /api/employees/directory (read-only contact directory)
# ------------------------------------------------------------------
@employees_bp.route("/directory", methods=["GET"])
@jwt_required
def get_directory(current_user_id, current_user_role):
    """
    Get contact directory with scoping:
    - Admin: All employees
    - Line Manager: Direct reports and employees belonging to departments they manage
    - Employee: Only employees belonging to the same department
    """
    from models import Department
    
    current_user = User.query.get(current_user_id)
    if not current_user:
        return jsonify({"error": "User not found."}), 404
        
    query = User.query.filter_by(is_active=True) # Directory only lists active users
    
    is_lm = getattr(current_user, 'is_line_manager', False)
    
    if current_user_role == "Admin":
        # Can see everyone
        pass
    elif is_lm:
        # Line Managers can see:
        # 1. Admins (role == "Admin")
        # 2. Other Line Managers (is_line_manager == True)
        # 3. Direct reports, departments they manage, or themselves
        # 4. Employees in their own department
        managed_depts = Department.query.filter_by(manager_id=current_user_id).all()
        managed_dept_ids = [d.id for d in managed_depts]
        
        conds = [
            (User.role == "Admin"),
            (User.is_line_manager == True),
            (User.manager_id == current_user_id),
            (User.id == current_user_id)
        ]
        if current_user.department_id is not None:
            conds.append(User.department_id == current_user.department_id)
        if managed_dept_ids:
            conds.append(User.department_id.in_(managed_dept_ids))
            
        final_cond = conds[0]
        for cond in conds[1:]:
            final_cond = final_cond | cond
            
        query = query.filter(final_cond)
    else:
        # Regular employee: Only employees belonging to the same department
        if current_user.department_id:
            query = query.filter_by(department_id=current_user.department_id)
        else:
            # If they have no department, they only see themselves
            query = query.filter_by(id=current_user_id)

    # Search & filters
    search = request.args.get("search", "").strip()
    department_id = request.args.get("department_id", type=int)

    if search:
        like = f"%{search}%"
        query = query.filter(
            (User.name.ilike(like)) | 
            (User.employee_id.ilike(like)) | 
            (User.email.ilike(like)) | 
            (User.phone_number.ilike(like))
        )
        
    if department_id:
        if current_user_role == "Admin" or is_lm:
            query = query.filter_by(department_id=department_id)
        else:
            if department_id == current_user.department_id:
                query = query.filter_by(department_id=department_id)
            else:
                return jsonify({"employees": [], "total": 0}), 200

    employees_list = query.order_by(User.name).all()
    
    results = []
    for e in employees_list:
        results.append({
            "id": e.id,
            "employee_id": e.employee_id,
            "name": e.name,
            "email": e.email,
            "phone_number": e.phone_number,
            "department_name": e.department.name if e.department else None,
            "department_id": e.department_id,
            "rank": e.rank,
            "role": e.role,
            "is_line_manager": e.is_line_manager,
            "is_active": e.is_active,
            "photo_url": e.photo_url,
            "availability_status": _get_availability_status(e)
        })
        
    return jsonify({
        "employees": results,
        "total": len(results)
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
@jwt_required
def create_employee(current_user_id, current_user_role):
    """
    Create a new employee account.
    - Admin: Full rights
    - Line Manager: Can create employees, automatically assigned to themselves.
    """
    creator = User.query.get(current_user_id)
    if current_user_role != "Admin" and (not creator or not getattr(creator, 'is_line_manager', False)):
        return jsonify({"error": "Admin or Line Manager access required."}), 403

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

    if current_user_role != "Admin":
        manager_id = current_user_id
        role = "Employee"
    else:
        manager_id = data.get("manager_id")
        role = data.get("role", "Employee")

    if manager_id:
        manager = User.query.get(manager_id)
        if not manager or not manager.is_active:
            return jsonify({"error": "Selected manager does not exist or is inactive."}), 422

    employee = User(
        employee_id=data.get("employee_id") or generate_department_employee_id(data.get("department_id")),
        email=email,
        password_hash=pw_hash,
        role=role,
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
        phone_number=data.get("phone_number"),
        gender=data.get("gender", "Male"),
    )
    db.session.add(employee)
    db.session.flush()  # Flush to get employee.id for leave balances

    # Initialise leave balances (APL and WFH) for the new employee
    gender = employee.gender or "Male"
    apl_allocated = 20
    wfh_allocated = 5 if gender == "Female" else 4

    db.session.add(LeaveBalance(
        employee_id=employee.id,
        leave_type="APL",
        allocated=apl_allocated,
        used=0,
        remaining=apl_allocated,
    ))
    db.session.add(LeaveBalance(
        employee_id=employee.id,
        leave_type="WFH",
        allocated=wfh_allocated,
        used=0,
        remaining=wfh_allocated,
    ))

    # Initialise comp-off balance for the new employee
    cob = CompOffBalance(
        employee_id=employee.id,
        allocated=0,
        used=0,
        remaining=0
    )
    db.session.add(cob)

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
    current_user = User.query.get(current_user_id)
    is_line_manager_of_report = (
        current_user and 
        getattr(current_user, 'is_line_manager', False) and 
        employee.manager_id == current_user_id
    )

    if current_user_role != "Admin" and current_user_id != emp_id and not is_line_manager_of_report:
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

    emp_data = employee.to_dict(include_sensitive=(current_user_role == "Admin" or current_user_id == emp_id or is_line_manager_of_report))
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
    employee = User.query.get_or_404(emp_id)
    if employee.role == "Admin" and current_user_id != emp_id:
        return jsonify({"error": "Editing other Admin accounts is not allowed."}), 403

    current_user = User.query.get(current_user_id)
    is_line_manager_of_report = (
        current_user and 
        getattr(current_user, 'is_line_manager', False) and 
        employee.manager_id == current_user_id
    )

    if current_user_role != "Admin" and current_user_id != emp_id and not is_line_manager_of_report:
        return jsonify({"error": "Access denied."}), 403

    data = request.get_json(silent=True) or {}

    if "experience_summary" in data:
        exp = data["experience_summary"]
        if exp and len(str(exp)) > 5000:
            return jsonify({"error": "Experience summary must be under 5000 characters."}), 422

    if current_user_role == "Admin" or is_line_manager_of_report:
        # Admin or Line Manager can change these fields
        admin_fields = [
            "name", "fathers_name", "dob", "blood_group",
            "address", "permanent_address", "current_address", "emergency_contact",
            "department_id", "date_of_joining", "salary", "rank",
            "aadhar_number", "is_active", "phone_number",
            "bio", "experience_summary", "gender",
        ]
        if current_user_role == "Admin":
            admin_fields.append("role")
            admin_fields.append("is_line_manager")

        for field in admin_fields:
            if field in data:
                setattr(employee, field, data[field])

        if current_user_role == "Admin" and "manager_id" in data:
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

        # Allow password reset by admin or line manager
        if data.get("password"):
            employee.password_hash = bcrypt.hashpw(
                data["password"].encode("utf-8"), bcrypt.gensalt()
            ).decode("utf-8")
    else:
        # Employee self-editable fields only
        self_fields = ["address", "current_address", "emergency_contact", "phone_number", "bio", "experience_summary", "gender"]
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
    if employee.role == "Admin" and current_user_id != emp_id:
        return jsonify({"error": "Editing other Admin accounts is not allowed."}), 403

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
    file_dest = os.path.join(upload_path, filename)
    file.save(file_dest)

    new_resume_url = f"/api/employees/uploads/{filename}"

    if current_user_role == "Admin":
        # Admin upload is immediately active
        employee.resume_url = new_resume_url
        db.session.commit()
        
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
    else:
        # Non-admin upload creates an Approval Request
        from routes.profile import determine_approver
        from models import ResumeUpdateRequest, ApprovalRequest
        
        approver_id = determine_approver(employee)
        if not approver_id:
            return jsonify({"error": "No active approver (manager or admin) could be found."}), 500

        try:
            # Create ResumeUpdateRequest
            req_update = ResumeUpdateRequest(
                employee_id=emp_id,
                resume_url=new_resume_url,
                status="Pending"
            )
            db.session.add(req_update)
            db.session.flush()

            # Create ApprovalRequest
            app_req = ApprovalRequest(
                requester_id=emp_id,
                approver_id=approver_id,
                module_type="ResumeUpdate",
                target_id=req_update.id,
                status="Pending"
            )
            db.session.add(app_req)
            db.session.flush()

            req_update.approval_request_id = app_req.id
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": f"Failed to submit resume update request: {str(e)}"}), 500

        return jsonify({
            "message": "Resume upload submitted for approval.",
            "status": "Pending",
            "resume_url": employee.resume_url  # remains the old one for now
        }), 200


# ------------------------------------------------------------------
# GET /api/employees/uploads/<filename>  (serve uploaded files)
# ------------------------------------------------------------------
@employees_bp.route("/uploads/<path:filename>", methods=["GET"])
def serve_resume(filename):
    """Serve uploaded resume files (authenticated) or avatars (public)."""
    parts = filename.split("_")
    
    # Avatars do not require JWT authentication to support browser <img> rendering
    if len(parts) >= 2 and parts[0] == "avatar":
        upload_path = current_app.config["UPLOAD_FOLDER"]
        return send_from_directory(upload_path, filename)

    # Resumes require JWT verification and ownership/role check
    from utils.decorators import _extract_token, _decode_token
    import jwt

    token = _extract_token()
    if not token:
        # Fallback to query parameter auth_token to allow opening in a new tab/iframe
        token = request.args.get("auth_token")
        
    if not token:
        return jsonify({"error": "Authorization token is missing."}), 401
    try:
        payload = _decode_token(token)
    except jwt.ExpiredSignatureError:
        return jsonify({"error": "Token has expired. Please log in again."}), 401
    except jwt.InvalidTokenError:
        return jsonify({"error": "Invalid token."}), 401

    current_user_id = payload["user_id"]
    current_user_role = payload["role"]

    if current_user_role != "Admin":
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


# ------------------------------------------------------------------
# POST /api/employees/<id>/photo
# ------------------------------------------------------------------
@employees_bp.route("/<int:emp_id>/photo", methods=["POST"])
@jwt_required
def upload_photo(emp_id, current_user_id, current_user_role):
    """Upload a profile photo image for an employee."""
    employee = User.query.get_or_404(emp_id)
    if employee.role == "Admin" and current_user_id != emp_id:
        return jsonify({"error": "Editing other Admin accounts is not allowed."}), 403

    # Only Admin or the user themselves can upload
    if current_user_role != "Admin" and current_user_id != emp_id:
        return jsonify({"error": "Unauthorized. You can only upload your own profile photo."}), 403

    if "photo" not in request.files:
        return jsonify({"error": "No file part in the request."}), 400

    file = request.files["photo"]
    if file.filename == "":
        return jsonify({"error": "No file selected."}), 400

    # Validate image extension
    allowed_image_exts = {"png", "jpg", "jpeg", "webp"}
    if not ("." in file.filename and file.filename.rsplit(".", 1)[1].lower() in allowed_image_exts):
        return jsonify({"error": "File type not allowed. Use PNG, JPG, JPEG, or WEBP."}), 422

    filename = secure_filename(f"avatar_{emp_id}_{file.filename}")
    upload_path = current_app.config["UPLOAD_FOLDER"]
    os.makedirs(upload_path, exist_ok=True)
    
    # Optional: Delete any old avatar if it exists
    if employee.photo_url:
        old_filename = employee.photo_url.split("/")[-1]
        old_path = os.path.join(upload_path, old_filename)
        if os.path.exists(old_path):
            try:
                os.remove(old_path)
            except Exception:
                pass

    file.save(os.path.join(upload_path, filename))

    # Update database record
    employee.photo_url = f"/api/employees/uploads/{filename}"
    db.session.commit()

    return jsonify({"message": "Profile photo uploaded successfully.", "photo_url": employee.photo_url}), 200


# ------------------------------------------------------------------
# GET /api/employees/<id>/dashboard-details
# ------------------------------------------------------------------
@employees_bp.route("/<int:emp_id>/dashboard-details", methods=["GET"])
@jwt_required
def get_employee_dashboard_details(emp_id, current_user_id, current_user_role):
    """Retrieve details for the Employee Detail Dashboard (accessible by Admin or direct Line Manager)."""
    employee = User.query.get_or_404(emp_id)
    current_user = User.query.get(current_user_id)
    is_lm = current_user and getattr(current_user, 'is_line_manager', False) and employee.manager_id == current_user_id

    # Check permission: Admin, Line Manager of this employee, or the employee themselves
    if current_user_role != "Admin" and not is_lm and current_user_id != emp_id:
        return jsonify({"error": "Access denied. Only Admins, the direct Line Manager, or the employee themselves can view this."}), 403

    # Import other models locally to avoid circular dependencies
    from models import Attendance, Task, Timesheet, LeaveBalance

    # 1. Profile information
    profile = employee.to_dict(include_sensitive=True)
    profile["availability_status"] = _get_availability_status(employee)
    profile["upcoming_leave"] = _get_upcoming_leave(employee)

    # 2. Attendance history
    attendance_records = Attendance.query.filter_by(employee_id=emp_id).order_by(Attendance.date.desc()).all()
    attendance_history = [att.to_dict() for att in attendance_records]

    # 3. Tasks history
    tasks_records = Task.query.filter_by(employee_id=emp_id).order_by(Task.created_at.desc()).all()
    task_history = [task.to_dict() for task in tasks_records]

    # 4. Timesheet history
    timesheet_records = Timesheet.query.filter_by(employee_id=emp_id).order_by(Timesheet.date.desc()).all()
    timesheet_history = [ts.to_dict() for ts in timesheet_records]

    # 5. Leaves assigned vs taken
    leave_balances = LeaveBalance.query.filter_by(employee_id=emp_id).all()
    leave_summary = [lb.to_dict() for lb in leave_balances]

    return jsonify({
        "profile": profile,
        "attendance_history": attendance_history,
        "task_history": task_history,
        "timesheet_history": timesheet_history,
        "leave_summary": leave_summary
    }), 200


# ------------------------------------------------------------------
# DELETE /api/employees/<id>/photo
# ------------------------------------------------------------------
@employees_bp.route("/<int:emp_id>/photo", methods=["DELETE"])
@jwt_required
def delete_photo(emp_id, current_user_id, current_user_role):
    """Delete the profile photo for an employee and revert to default initials."""
    employee = User.query.get_or_404(emp_id)
    if employee.role == "Admin" and current_user_id != emp_id:
        return jsonify({"error": "Editing other Admin accounts is not allowed."}), 403

    # Only Admin or the user themselves can delete
    if current_user_role != "Admin" and current_user_id != emp_id:
        return jsonify({"error": "Unauthorized. You can only delete your own profile photo."}), 403

    if employee.photo_url:
        upload_path = current_app.config["UPLOAD_FOLDER"]
        filename = employee.photo_url.split("/")[-1]
        file_path = os.path.join(upload_path, filename)
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception:
                pass
        
        employee.photo_url = None
        db.session.commit()

    return jsonify({"message": "Profile photo deleted successfully."}), 200

