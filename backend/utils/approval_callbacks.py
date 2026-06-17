# backend/utils/approval_callbacks.py
"""
Callback Registry for the Generic Approval Engine.
Allows external modules to register functions that execute when an approval request is actioned.
"""

class ApprovalCallbackRegistry:
    _registry = {}

    @classmethod
    def register(cls, module_type):
        """Decorator to register a callback function for a specific module type."""
        def decorator(f):
            cls._registry[module_type] = f
            return f
        return decorator

    @classmethod
    def execute(cls, module_type, target_id, action, db_session):
        """Execute the registered callback function for the given module type."""
        handler = cls._registry.get(module_type)
        if handler:
            try:
                return handler(target_id, action, db_session)
            except Exception as e:
                # Log error or raise depending on transaction requirements
                raise RuntimeError(f"Approval callback failed for {module_type} on target {target_id}: {str(e)}")
        return True


# ------------------------------------------------------------------
# Handler for UserProfileUpdate module
# ------------------------------------------------------------------
@ApprovalCallbackRegistry.register("UserProfileUpdate")
def handle_user_profile_update(target_id, action, db_session):
    from models import UserProfileUpdate, User
    update_req = db_session.query(UserProfileUpdate).get(target_id)
    if not update_req:
        return False
        
    update_req.status = action
    
    if action == "Approved":
        user = db_session.query(User).get(update_req.employee_id)
        if user:
            for field, value in update_req.requested_changes.items():
                # Handle dob or date conversion if present (e.g. from string to date object)
                # (but frontend should send clean data, handle basic conversions)
                from datetime import date
                if field == "dob" and isinstance(value, str):
                    try:
                        value = date.fromisoformat(value)
                    except ValueError:
                        pass
                setattr(user, field, value)
    return True


# ------------------------------------------------------------------
# Handler for WorkTransfer module
# ------------------------------------------------------------------
@ApprovalCallbackRegistry.register("WorkTransfer")
def handle_work_transfer(target_id, action, db_session):
    from models import WorkTransferRequest, User
    from utils.notification_service import create_notification
    
    wt = db_session.query(WorkTransferRequest).get(target_id)
    if not wt:
        return False
        
    wt.status = action
    
    # Send notifications about action
    try:
        requester = db_session.query(User).get(wt.requester_id)
        delegate = db_session.query(User).get(wt.delegate_to_id)
        
        # 1. Notify requester
        create_notification(
            user_id=wt.requester_id,
            title=f"Work Transfer Request {action}",
            content=f"Your request to delegate work to {delegate.name if delegate else 'delegate'} from {wt.start_date} to {wt.end_date} has been {action.lower()}.",
            notification_type="WorkTransfer",
            target_id=wt.id,
            action_url="/work-transfers"
        )
        
        # 2. Notify delegate
        create_notification(
            user_id=wt.delegate_to_id,
            title=f"Work Delegation {action}",
            content=f"{requester.name if requester else 'An employee'} has delegated work to you (Status: {action}).",
            notification_type="WorkTransfer",
            target_id=wt.id,
            action_url="/work-transfers"
        )
        
        # 3. Notify manager (who actioned it)
        if wt.approval_request and wt.approval_request.approver_id:
            create_notification(
                user_id=wt.approval_request.approver_id,
                title=f"Work Delegation Actioned: {action}",
                content=f"You have {action.lower()} the work delegation request from {requester.name if requester else 'employee'} to {delegate.name if delegate else 'delegate'}.",
                notification_type="WorkTransfer",
                target_id=wt.id,
                action_url="/work-transfers"
            )
    except Exception as e:
        print(f"[ERROR] Failed to send work transfer action notifications: {e}")
        
    return True


# ------------------------------------------------------------------
# Handler for CompOff module
# ------------------------------------------------------------------
@ApprovalCallbackRegistry.register("CompOff")
def handle_comp_off(target_id, action, db_session):
    from models import CompOffRequest, User
    from routes.comp_off import get_or_create_comp_off_balance
    from utils.notification_service import create_notification
    from datetime import datetime
    
    req = db_session.query(CompOffRequest).get(target_id)
    if not req:
        return False
        
    req.status = action
    req.actioned_at = datetime.utcnow()
    
    # Link comments from ApprovalRequest to rejection_reason if rejected
    if action == "Rejected" and req.approval_request:
        req.rejection_reason = req.approval_request.comments or "No comments provided."
        
    if action == "Approved":
        cob = get_or_create_comp_off_balance(req.employee_id, db_session=db_session)
        cob.allocated += 1
        cob.recalculate()
        
    # Notify employee
    try:
        user = db_session.query(User).get(req.employee_id)
        rejection_suffix = f" Reason: {req.rejection_reason}" if (action == "Rejected" and req.rejection_reason) else ""
        create_notification(
            user_id=req.employee_id,
            title=f"Comp-Off Request {action}",
            content=f"Your Comp-Off request for date {req.date_worked} has been {action.lower()}.{rejection_suffix}",
            notification_type="CompOff",
            target_id=req.id,
            action_url="/comp-off"
        )
    except Exception as e:
        print(f"[ERROR] Failed to send Comp-Off action notification: {e}")
        
    return True


# ------------------------------------------------------------------
# Handler for ResumeUpdate module
# ------------------------------------------------------------------
@ApprovalCallbackRegistry.register("ResumeUpdate")
def handle_resume_update(target_id, action, db_session):
    from models import ResumeUpdateRequest, User
    from utils.notification_service import create_notification
    
    update_req = db_session.query(ResumeUpdateRequest).get(target_id)
    if not update_req:
        return False
        
    update_req.status = action
    
    if action == "Approved":
        user = db_session.query(User).get(update_req.employee_id)
        if user:
            user.resume_url = update_req.resume_url
            
    # Notify employee
    try:
        create_notification(
            user_id=update_req.employee_id,
            title=f"Resume Update {action}",
            content=f"Your uploaded resume has been {action.lower()}.",
            notification_type="System",
            target_id=update_req.id,
            action_url="/profile"
        )
    except Exception as e:
        print(f"[ERROR] Failed to send Resume Update action notification: {e}")
        
    return True

