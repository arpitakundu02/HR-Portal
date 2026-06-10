"""
backend/routes/departments.py
------------------------------
Department management endpoints.

Endpoints:
  GET  /api/departments        - List all departments (authenticated)
  POST /api/departments        - Admin: Create a department
  PUT  /api/departments/<id>   - Admin: Update a department
  DELETE /api/departments/<id> - Admin: Delete a department
"""

from flask import Blueprint, request, jsonify
from models import Department
from extensions import db
from utils.decorators import jwt_required, admin_required

departments_bp = Blueprint("departments", __name__)

# Default departments to seed on first run (handled in init_db.py)
DEFAULT_DEPARTMENTS = [
    "Research", "Tech", "GIS", "Data Scientist",
    "Broker", "Execution", "Account", "Management",
]


# ------------------------------------------------------------------
# GET /api/departments
# ------------------------------------------------------------------
@departments_bp.route("/", methods=["GET"])
@jwt_required
def list_departments(current_user_id, current_user_role):
    """Return all departments."""
    departments = Department.query.order_by(Department.name).all()
    return jsonify([d.to_dict() for d in departments]), 200


# ------------------------------------------------------------------
# POST /api/departments
# ------------------------------------------------------------------
@departments_bp.route("/", methods=["POST"])
@admin_required
def create_department(current_user_id, current_user_role):
    """Admin-only: Create a new department."""
    data = request.get_json(silent=True)
    if not data or not data.get("name"):
        return jsonify({"error": "'name' is required."}), 422

    name = data["name"].strip()
    if Department.query.filter_by(name=name).first():
        return jsonify({"error": f"Department '{name}' already exists."}), 409

    dept = Department(name=name, description=data.get("description"))
    db.session.add(dept)
    db.session.commit()
    return jsonify(dept.to_dict()), 201


# ------------------------------------------------------------------
# PUT /api/departments/<id>
# ------------------------------------------------------------------
@departments_bp.route("/<int:dept_id>", methods=["PUT"])
@admin_required
def update_department(dept_id, current_user_id, current_user_role):
    """Admin-only: Update department name or description."""
    dept = Department.query.get_or_404(dept_id)
    data = request.get_json(silent=True) or {}

    if "name" in data:
        dept.name = data["name"].strip()
    if "description" in data:
        dept.description = data["description"]

    db.session.commit()
    return jsonify(dept.to_dict()), 200


# ------------------------------------------------------------------
# DELETE /api/departments/<id>
# ------------------------------------------------------------------
@departments_bp.route("/<int:dept_id>", methods=["DELETE"])
@admin_required
def delete_department(dept_id, current_user_id, current_user_role):
    """Admin-only: Delete a department (only if no employees assigned)."""
    dept = Department.query.get_or_404(dept_id)

    if dept.employees.count() > 0:
        return jsonify({
            "error": "Cannot delete department with assigned employees. Reassign them first."
        }), 409

    db.session.delete(dept)
    db.session.commit()
    return jsonify({"message": f"Department '{dept.name}' deleted."}), 200


# ------------------------------------------------------------------
# GET /api/departments/<id>
# ------------------------------------------------------------------
@departments_bp.route("/<int:dept_id>", methods=["GET"])
@jwt_required
def get_department_details(dept_id, current_user_id, current_user_role):
    """Return department aggregated details and statistics."""
    from datetime import date, datetime
    from models import User, Attendance, Leave, Task, Meeting

    dept = Department.query.get_or_404(dept_id)

    # 1. Employees
    employees = dept.employees.all()
    emp_ids = [e.id for e in employees]

    # 2. Today's attendance
    today = date.today()
    present_today = 0
    if emp_ids:
        present_today = Attendance.query.filter(
            Attendance.employee_id.in_(emp_ids),
            Attendance.date == today,
            Attendance.check_in != None
        ).count()

    # 3. Employees on leave today
    on_leave_today = 0
    if emp_ids:
        on_leave_today = Leave.query.filter(
            Leave.employee_id.in_(emp_ids),
            Leave.status == "Approved",
            Leave.start_date <= today,
            Leave.end_date >= today
        ).count()

    # 4. Tasks Stats
    total_tasks = 0
    pending_tasks = 0
    in_progress_tasks = 0
    completed_tasks = 0
    if emp_ids:
        total_tasks = Task.query.filter(Task.employee_id.in_(emp_ids)).count()
        pending_tasks = Task.query.filter(Task.employee_id.in_(emp_ids), Task.status == "Pending").count()
        in_progress_tasks = Task.query.filter(Task.employee_id.in_(emp_ids), Task.status == "In Progress").count()
        completed_tasks = Task.query.filter(Task.employee_id.in_(emp_ids), Task.status == "Completed").count()

    # 5. Leaves Stats
    pending_leaves = 0
    approved_leaves = 0
    rejected_leaves = 0
    if emp_ids:
        pending_leaves = Leave.query.filter(Leave.employee_id.in_(emp_ids), Leave.status == "Pending").count()
        approved_leaves = Leave.query.filter(Leave.employee_id.in_(emp_ids), Leave.status == "Approved").count()
        rejected_leaves = Leave.query.filter(Leave.employee_id.in_(emp_ids), Leave.status == "Rejected").count()

    # 6. Meetings
    now = datetime.utcnow()
    upcoming_meetings_query = Meeting.query.filter(
        Meeting.department_id == dept.id,
        Meeting.scheduled_at >= now
    )
    upcoming_meetings_count = upcoming_meetings_query.count()
    upcoming_meetings = upcoming_meetings_query.order_by(Meeting.scheduled_at.asc()).all()

    # Serialize employees
    serialized_employees = []
    for e in employees:
        serialized_employees.append({
            "id": e.id,
            "employee_id": e.employee_id,
            "name": e.name,
            "email": e.email,
            "role": e.role,
            "rank": e.rank,
            "is_active": e.is_active
        })

    # Serialize meetings
    serialized_meetings = [m.to_dict() for m in upcoming_meetings]

    return jsonify({
        "department": dept.to_dict(),
        "stats": {
            "total_employees": len(employees),
            "present_today": present_today,
            "on_leave_today": on_leave_today,
            "pending_tasks": pending_tasks,
            "completed_tasks": completed_tasks,
            "upcoming_meetings_count": upcoming_meetings_count
        },
        "employees": serialized_employees,
        "tasks": {
            "total": total_tasks,
            "pending": pending_tasks,
            "in_progress": in_progress_tasks,
            "completed": completed_tasks
        },
        "leaves": {
            "pending": pending_leaves,
            "approved": approved_leaves,
            "rejected": rejected_leaves
        },
        "meetings": serialized_meetings
    }), 200

