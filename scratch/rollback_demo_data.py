# scratch/rollback_demo_data.py
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))

from app import create_app
from extensions import db
from models import User, Department, Leave, LeaveBalance, Attendance, Task, Meeting, Announcement, Notification, ApprovalRequest, ApprovalLog, WorkTransferRequest, AttendanceAdjustment

def rollback():
    app = create_app()
    with app.app_context():
        print("[*] Starting rollback of demo seeded data...")
        
        # 1. Find all demo users
        demo_users = User.query.filter(User.employee_id.like("DEMO-%")).all()
        demo_user_ids = [u.id for u in demo_users]
        
        if not demo_user_ids:
            print("[!] No demo users found. Nothing to rollback.")
            return
            
        print(f"[*] Found {len(demo_user_ids)} demo users to delete.")
        
        # 2. Delete linked data explicitly to prevent foreign key issues
        # Attendance records
        att_deleted = Attendance.query.filter(Attendance.employee_id.in_(demo_user_ids)).delete(synchronize_session=False)
        print(f"[✓] Deleted {att_deleted} attendance records.")
        
        # Attendance adjustments
        adj_deleted = AttendanceAdjustment.query.filter(AttendanceAdjustment.employee_id.in_(demo_user_ids)).delete(synchronize_session=False)
        print(f"[✓] Deleted {adj_deleted} attendance adjustments.")
        
        # Leave requests
        leaves_deleted = Leave.query.filter(Leave.employee_id.in_(demo_user_ids)).delete(synchronize_session=False)
        print(f"[✓] Deleted {leaves_deleted} leave requests.")
        
        # Leave balances
        bal_deleted = LeaveBalance.query.filter(LeaveBalance.employee_id.in_(demo_user_ids)).delete(synchronize_session=False)
        print(f"[✓] Deleted {bal_deleted} leave balances.")
        
        # Tasks
        tasks_deleted = Task.query.filter(Task.employee_id.in_(demo_user_ids)).delete(synchronize_session=False)
        print(f"[✓] Deleted {tasks_deleted} tasks.")
        
        # Notifications
        notif_deleted = Notification.query.filter(Notification.user_id.in_(demo_user_ids)).delete(synchronize_session=False)
        print(f"[✓] Deleted {notif_deleted} notifications.")
        
        # Work transfer requests (where user is requester or delegate)
        wt_deleted = WorkTransferRequest.query.filter(
            db.or_(
                WorkTransferRequest.requester_id.in_(demo_user_ids),
                WorkTransferRequest.delegate_to_id.in_(demo_user_ids)
            )
        ).delete(synchronize_session=False)
        print(f"[✓] Deleted {wt_deleted} work transfer requests.")
        
        # Approval requests (where user is requester or approver)
        app_req_deleted = ApprovalRequest.query.filter(
            db.or_(
                ApprovalRequest.requester_id.in_(demo_user_ids),
                ApprovalRequest.approver_id.in_(demo_user_ids)
            )
        ).delete(synchronize_session=False)
        print(f"[✓] Deleted {app_req_deleted} approval requests.")
        
        # Unlink department managers if they were demo users
        for dept in Department.query.all():
            if dept.manager_id in demo_user_ids:
                dept.manager_id = None
                
        # Unlink managers of any remaining users if they were demo users
        for u in User.query.all():
            if u.manager_id in demo_user_ids:
                u.manager_id = None
                
        db.session.commit()
        
        # 3. Delete demo users
        users_deleted = User.query.filter(User.id.in_(demo_user_ids)).delete(synchronize_session=False)
        print(f"[✓] Deleted {users_deleted} demo users.")
        
        # 4. Clean up Announcements created by Admin/demo users during seeding if needed
        # (Since announcements don't reference employee FK in a cascade restriction, we can delete the specific ones we seeded)
        ann_deleted = Announcement.query.filter(
            Announcement.title.in_(["HR Portal Upgrade Complete!", "Policy Update: Regularization limits"])
        ).delete(synchronize_session=False)
        print(f"[✓] Deleted {ann_deleted} announcements.")
        
        db.session.commit()
        print("[✓] Rollback completed successfully!")

if __name__ == "__main__":
    rollback()
