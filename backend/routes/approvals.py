# backend/routes/approvals.py
"""
backend/routes/approvals.py
----------------------------
Generic Approval Engine endpoints.
Handles listing pending approvals and actioning request transitions.
"""

from datetime import datetime
from flask import Blueprint, request, jsonify
from models import ApprovalRequest, ApprovalLog, User
from extensions import db
from utils.decorators import jwt_required
from utils.approval_callbacks import ApprovalCallbackRegistry

approvals_bp = Blueprint("approvals", __name__)


# ------------------------------------------------------------------
# GET /api/approvals/pending
# ------------------------------------------------------------------
@approvals_bp.route("/pending", methods=["GET"])
@jwt_required
def get_pending_approvals(current_user_id, current_user_role):
    """
    Get all pending approval requests assigned to the current user or delegated to them.
    """
    from datetime import date
    from models import WorkTransferRequest
    today = date.today()
    
    # Find users who have actively delegated approvals to the current user
    delegated_users = db.session.query(WorkTransferRequest.requester_id).filter(
        WorkTransferRequest.delegate_to_id == current_user_id,
        WorkTransferRequest.status == "Approved",
        WorkTransferRequest.start_date <= today,
        WorkTransferRequest.end_date >= today,
        WorkTransferRequest.transfer_approvals == True
    ).all()
    delegator_ids = [r[0] for r in delegated_users]
    
    if current_user_role == "Admin":
        conditions = [
            ApprovalRequest.approver_id == current_user_id,
            ApprovalRequest.module_type == "ResumeUpdate"
        ]
        if delegator_ids:
            conditions.append(ApprovalRequest.approver_id.in_(delegator_ids))
        query = ApprovalRequest.query.filter(db.or_(*conditions))
    else:
        if delegator_ids:
            query = ApprovalRequest.query.filter(
                db.or_(
                    ApprovalRequest.approver_id == current_user_id,
                    db.and_(
                        ApprovalRequest.approver_id.in_(delegator_ids),
                        ApprovalRequest.status == "Pending"
                    )
                )
            )
        else:
            query = ApprovalRequest.query.filter(
                ApprovalRequest.approver_id == current_user_id
            )
    
    query = query.filter(ApprovalRequest.status == "Pending")
    
    requests = query.order_by(ApprovalRequest.created_at.desc()).all()
    return jsonify([req.to_dict() for req in requests]), 200


# ------------------------------------------------------------------
# POST /api/approvals/<id>/action
# ------------------------------------------------------------------
@approvals_bp.route("/<int:request_id>/action", methods=["POST"])
@jwt_required
def action_approval(request_id, current_user_id, current_user_role):
    """
    Action (Approve/Reject) a pending approval request.
    Validates that the current user is the assigned approver or active delegate.
    """
    req = ApprovalRequest.query.get_or_404(request_id)
    
    # Restrict actions to the designated approver, active delegate, or Admin for ResumeUpdate
    is_authorized = (req.approver_id == current_user_id) or (current_user_role == "Admin" and req.module_type == "ResumeUpdate")
    if not is_authorized:
        from datetime import date
        from models import WorkTransferRequest
        today = date.today()
        is_authorized = db.session.query(db.exists().where(db.and_(
            WorkTransferRequest.requester_id == req.approver_id,
            WorkTransferRequest.delegate_to_id == current_user_id,
            WorkTransferRequest.status == "Approved",
            WorkTransferRequest.start_date <= today,
            WorkTransferRequest.end_date >= today,
            WorkTransferRequest.transfer_approvals == True
        ))).scalar()
        
    if not is_authorized:
        return jsonify({"error": "Access denied. You are not the assigned approver or active delegate for this request."}), 403
        
    if req.requester_id == current_user_id:
        return jsonify({"error": "Access denied. You cannot approve or action your own requests."}), 403
        
    if req.status != "Pending":
        return jsonify({"error": "This request has already been actioned."}), 400
        
    data = request.get_json(silent=True)
    if not data or data.get("status") not in ("Approved", "Rejected"):
        return jsonify({"error": "'status' must be 'Approved' or 'Rejected'."}), 422
        
    new_status = data["status"]
    comments = data.get("comments", "").strip()
    
    # Store old status for logging
    old_status = req.status
    
    # Begin transaction
    try:
        # 1. Update request status
        req.status = new_status
        req.comments = comments if comments else None
        req.actioned_at = datetime.utcnow()
        
        # 2. Write log entry
        log_entry = ApprovalLog(
            approval_request_id=req.id,
            actioner_id=current_user_id,
            old_status=old_status,
            new_status=new_status,
            comments=req.comments
        )
        db.session.add(log_entry)
        
        # 3. Trigger registered callback
        ApprovalCallbackRegistry.execute(
            module_type=req.module_type,
            target_id=req.target_id,
            action=new_status,
            db_session=db.session
        )
        
        db.session.commit()
    except Exception as exc:
        db.session.rollback()
        return jsonify({"error": f"Failed to process approval action: {str(exc)}"}), 500
        
    return jsonify({"message": f"Request marked as {new_status}.", "request": req.to_dict()}), 200
