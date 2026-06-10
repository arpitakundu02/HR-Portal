# backend/routes/work_transfers.py
"""
backend/routes/work_transfers.py
--------------------------------
Endpoints for managing work transfer and delegation requests.
"""

from datetime import datetime, date
from flask import Blueprint, request, jsonify
from extensions import db
from models import WorkTransferRequest, User, ApprovalRequest, Department
from utils.decorators import jwt_required
from utils.notification_service import create_notification

work_transfers_bp = Blueprint("work_transfers", __name__)

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

@work_transfers_bp.route("/", methods=["POST"])
@jwt_required
def create_transfer_request(current_user_id, current_user_role):
    """
    Create a new work transfer request.
    Routes to manager for approval and triggers in-app notifications.
    """
    data = request.get_json(silent=True) or {}
    
    delegate_to_id = data.get("delegate_to_id")
    start_date_str = data.get("start_date")
    end_date_str = data.get("end_date")
    
    if not delegate_to_id or not start_date_str or not end_date_str:
        return jsonify({"error": "delegate_to_id, start_date, and end_date are required."}), 422
        
    if delegate_to_id == current_user_id:
        return jsonify({"error": "You cannot delegate work to yourself."}), 422
        
    delegate = User.query.get(delegate_to_id)
    if not delegate or not delegate.is_active:
        return jsonify({"error": "Selected delegate does not exist or is inactive."}), 422
        
    try:
        start_date = date.fromisoformat(start_date_str)
        end_date = date.fromisoformat(end_date_str)
    except ValueError:
        return jsonify({"error": "Dates must be in YYYY-MM-DD format."}), 422
        
    if start_date > end_date:
        return jsonify({"error": "start_date cannot be after end_date."}), 422
        
    transfer_tasks = bool(data.get("transfer_tasks", False))
    transfer_approvals = bool(data.get("transfer_approvals", False))
    transfer_meetings = bool(data.get("transfer_meetings", False))
    
    if not (transfer_tasks or transfer_approvals or transfer_meetings):
        return jsonify({"error": "At least one delegation option (tasks, approvals, meetings) must be enabled."}), 422
        
    user = User.query.get_or_404(current_user_id)
    approver_id = determine_approver(user)
    if not approver_id:
        return jsonify({"error": "No active approver (manager or admin) could be found."}), 500
        
    # Check for overlapping requests
    overlap = WorkTransferRequest.query.filter(
        WorkTransferRequest.requester_id == current_user_id,
        WorkTransferRequest.status.in_(["Pending", "Approved"]),
        WorkTransferRequest.start_date <= end_date,
        WorkTransferRequest.end_date >= start_date
    ).first()
    if overlap:
        return jsonify({"error": "You already have a pending or approved work transfer that overlaps with these dates."}), 409
        
    try:
        # 1. Create Work Transfer Request
        wt_req = WorkTransferRequest(
            requester_id=current_user_id,
            delegate_to_id=delegate_to_id,
            start_date=start_date,
            end_date=end_date,
            transfer_tasks=transfer_tasks,
            transfer_approvals=transfer_approvals,
            transfer_meetings=transfer_meetings,
            status="Pending"
        )
        db.session.add(wt_req)
        db.session.flush()
        
        # 2. Create corresponding ApprovalRequest
        approval_req = ApprovalRequest(
            requester_id=current_user_id,
            approver_id=approver_id,
            module_type="WorkTransfer",
            target_id=wt_req.id,
            status="Pending"
        )
        db.session.add(approval_req)
        db.session.flush()
        
        wt_req.approval_request_id = approval_req.id
        db.session.commit()
        
        # 3. Trigger notifications
        # Notify Requester
        create_notification(
            user_id=current_user_id,
            title="Work Transfer Request Submitted",
            content=f"Your request to delegate work to {delegate.name} from {start_date_str} to {end_date_str} is pending approval.",
            notification_type="WorkTransfer",
            target_id=wt_req.id,
            action_url="/work-transfers"
        )
        # Notify Delegate
        create_notification(
            user_id=delegate_to_id,
            title="Work Delegation Request",
            content=f"{user.name} wants to delegate work to you from {start_date_str} to {end_date_str}.",
            notification_type="WorkTransfer",
            target_id=wt_req.id,
            action_url="/work-transfers"
        )
        # Notify Manager
        create_notification(
            user_id=approver_id,
            title="Work Delegation Approval Required",
            content=f"{user.name} has requested work delegation to {delegate.name} from {start_date_str} to {end_date_str}.",
            notification_type="WorkTransfer",
            target_id=wt_req.id,
            action_url="/work-transfers"
        )
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to create work transfer request: {str(e)}"}), 500
        
    return jsonify(wt_req.to_dict()), 201

@work_transfers_bp.route("/", methods=["GET"])
@jwt_required
def get_transfer_requests(current_user_id, current_user_role):
    """
    List work transfer requests.
    - Admin: All requests.
    - Employee: Requests where they are the requester OR the delegate.
    """
    if current_user_role == "Admin":
        requests = WorkTransferRequest.query.order_by(WorkTransferRequest.created_at.desc()).all()
    else:
        requests = WorkTransferRequest.query.filter(
            db.or_(
                WorkTransferRequest.requester_id == current_user_id,
                WorkTransferRequest.delegate_to_id == current_user_id
            )
        ).order_by(WorkTransferRequest.created_at.desc()).all()
        
    my_requests = [r.to_dict() for r in requests if r.requester_id == current_user_id or current_user_role == "Admin"]
    received_transfers = [r.to_dict() for r in requests if r.delegate_to_id == current_user_id]
    
    return jsonify({
        "my_requests": my_requests,
        "received_transfers": received_transfers
    }), 200
