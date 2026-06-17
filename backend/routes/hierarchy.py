# backend/routes/hierarchy.py
"""
backend/routes/hierarchy.py
---------------------------
Blueprint for retrieving all active employees for Organization Chart rendering.
"""

from flask import Blueprint, jsonify
from models import User
from utils.decorators import jwt_required

hierarchy_bp = Blueprint("hierarchy", __name__)

@hierarchy_bp.route("", methods=["GET"])
@jwt_required
def get_hierarchy(current_user_id, current_user_role):
    """
    GET /api/hierarchy
    Get flat list of active employee nodes containing manager links for Org Chart tree creation.
    """
    users = User.query.filter_by(is_active=True).all()
    nodes = []
    for u in users:
        nodes.append({
            "id": u.id,
            "name": u.name,
            "employee_id": u.employee_id,
            "department_name": u.department.name if u.department else None,
            "department_id": u.department_id,
            "rank": u.rank,  # Rank is the designation
            "manager_id": u.manager_id,
            "manager_name": u.manager.name if u.manager else None,
            "role": u.role,
            "is_line_manager": u.is_line_manager
        })
    return jsonify(nodes), 200
