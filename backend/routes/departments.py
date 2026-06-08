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
