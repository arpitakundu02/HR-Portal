# backend/routes/profile.py
"""
backend/routes/profile.py
-------------------------
Routes for employee profile update requests and approvals.
"""

from datetime import datetime, date
from flask import Blueprint, request, jsonify
from extensions import db
from models import User, UserProfileUpdate, ApprovalRequest, Department
from utils.decorators import jwt_required

profile_bp = Blueprint("profile", __name__)

SAFE_PROFILE_FIELDS = {
    "name", "fathers_name", "dob", "blood_group",
    "address", "permanent_address", "current_address", "emergency_contact",
    "aadhar_number"
}

def determine_approver(user):
    # 1. Direct manager if manager_id exists and is active
    if user.manager_id:
        manager = User.query.get(user.manager_id)
        if manager and manager.is_active:
            return manager.id
            
    # 2. Department manager if available and is active
    if user.department_id:
        dept = Department.query.get(user.department_id)
        if dept and dept.manager_id:
            dept_mgr = User.query.get(dept.manager_id)
            if dept_mgr and dept_mgr.is_active:
                return dept_mgr.id
                
    # 3. Admin fallback (find first active Admin)
    admin = User.query.filter_by(role="Admin", is_active=True).first()
    if admin:
        return admin.id
        
    return None

@profile_bp.route("/update-request", methods=["POST"])
@jwt_required
def create_profile_update_request(current_user_id, current_user_role):
    """
    Submit a profile update request. Creates a pending profile update and 
    attaches an ApprovalRequest routed to the manager/department head/admin.
    """
    data = request.get_json(silent=True) or {}
    requested_changes = data.get("requested_changes")
    
    if not requested_changes or not isinstance(requested_changes, dict):
        return jsonify({"error": "requested_changes must be a JSON object."}), 422
        
    user = User.query.get_or_404(current_user_id)
    
    # Check if there is already a pending profile update request for this user
    existing_pending = UserProfileUpdate.query.filter_by(
        employee_id=current_user_id,
        status="Pending"
    ).first()
    if existing_pending:
        return jsonify({"error": "You already have a pending profile update request."}), 409
        
    # Validate fields and capture original values
    original_values = {}
    cleaned_changes = {}
    for field, new_val in requested_changes.items():
        if field not in SAFE_PROFILE_FIELDS:
            return jsonify({"error": f"Field '{field}' is not editable or allowed for approval updates."}), 400
            
        cleaned_changes[field] = new_val
        orig_val = getattr(user, field)
        if isinstance(orig_val, date):
            original_values[field] = orig_val.isoformat()
        else:
            original_values[field] = orig_val
            
    if not cleaned_changes:
        return jsonify({"error": "No valid changes requested."}), 422
        
    approver_id = determine_approver(user)
    if not approver_id:
        return jsonify({"error": "No active approver (manager or admin) could be found."}), 500
        
    try:
        # 1. Create Profile Update record
        profile_update = UserProfileUpdate(
            employee_id=current_user_id,
            requested_changes=cleaned_changes,
            original_values=original_values,
            status="Pending"
        )
        db.session.add(profile_update)
        db.session.flush() # Ensure we get profile_update.id
        
        # 2. Automatically create ApprovalRequest
        approval_req = ApprovalRequest(
            requester_id=current_user_id,
            approver_id=approver_id,
            module_type="UserProfileUpdate",
            target_id=profile_update.id,
            status="Pending"
        )
        db.session.add(approval_req)
        db.session.flush() # Ensure we get approval_req.id
        
        # 3. Link them together
        profile_update.approval_request_id = approval_req.id
        db.session.commit()
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to submit profile update request: {str(e)}"}), 500
        
    return jsonify({
        "message": "Profile update request submitted successfully.",
        "request": profile_update.to_dict()
    }), 201

@profile_bp.route("/update-request/history", methods=["GET"])
@jwt_required
def get_profile_update_history(current_user_id, current_user_role):
    """
    Get the history of profile update requests for the logged-in employee.
    """
    updates = UserProfileUpdate.query.filter_by(
        employee_id=current_user_id
    ).order_by(UserProfileUpdate.created_at.desc()).all()
    
    return jsonify([upd.to_dict() for upd in updates]), 200
