import os
import sys
import json
from datetime import datetime, timedelta, date

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))

from app import create_app
from extensions import db
from models import User, Leave, LeaveBalance, Notification, ApprovalRequest

def run_workflow():
    app = create_app()
    with app.app_context():
        # Setup test data
        employee = User(
            employee_id="TEST-LV-01",
            email="test_lv@company.com",
            name="Leave Tester",
            role="Employee",
            password_hash="hashed"
        )
        manager = User(
            employee_id="TEST-LV-MGR",
            email="test_lv_mgr@company.com",
            name="Leave Manager",
            role="Employee",
            password_hash="hashed"
        )
        delegate = User(
            employee_id="TEST-LV-DEL",
            email="test_lv_del@company.com",
            name="Leave Delegate",
            role="Employee",
            password_hash="hashed"
        )
        db.session.add_all([employee, manager, delegate])
        db.session.commit()
        
        # Create department
        from models import Department
        dept = Department(name="Leave Department", manager_id=manager.id)
        db.session.add(dept)
        db.session.commit()

        employee.manager_id = manager.id
        employee.department_id = dept.id
        delegate.department_id = dept.id
        db.session.commit()

        # Allocate Leave Balances
        balance = LeaveBalance(employee_id=employee.id, leave_type="APL", allocated=10, used=0, remaining=10)
        db.session.add(balance)
        db.session.commit()

        # Generate JWT client tokens
        import jwt
        token = jwt.encode(
            {"user_id": employee.id, "role": "Employee", "exp": datetime.utcnow() + timedelta(hours=1)},
            app.config["JWT_SECRET_KEY"],
            algorithm="HS256"
        )
        mgr_token = jwt.encode(
            {"user_id": manager.id, "role": "Employee", "exp": datetime.utcnow() + timedelta(hours=1)},
            app.config["JWT_SECRET_KEY"],
            algorithm="HS256"
        )

        client = app.test_client()

        # 1. Submit Leave request
        start_date = (date.today() + timedelta(days=5)).isoformat()
        end_date = (date.today() + timedelta(days=7)).isoformat()
        res = client.post("/api/leaves/apply",
                          headers={"Authorization": f"Bearer {token}"},
                          data=json.dumps({
                              "leave_type": "APL",
                              "start_date": start_date,
                              "end_date": end_date,
                              "reason": "Vacation",
                              "responsibility_transfer_id": delegate.id
                          }),
                          content_type="application/json")
        assert res.status_code == 201, f"Apply leave failed: {res.data}"
        lv_data = json.loads(res.data)

        # Verify DB state
        lv = Leave.query.get(lv_data["id"])
        assert lv.status == "Pending", "Leave status is not pending"

        # 3. Action Leave Request (Approve) (requires Admin)
        admin = User(
            employee_id="TEST-LV-ADM",
            email="test_lv_adm@company.com",
            name="Leave Admin",
            role="Admin",
            password_hash="hashed"
        )
        db.session.add(admin)
        db.session.commit()
        admin_token = jwt.encode(
            {"user_id": admin.id, "role": "Admin", "exp": datetime.utcnow() + timedelta(hours=1)},
            app.config["JWT_SECRET_KEY"],
            algorithm="HS256"
        )

        res = client.post(f"/api/leaves/requests/{lv.id}/action",
                          headers={"Authorization": f"Bearer {admin_token}"},
                          data=json.dumps({"status": "Approved"}),
                          content_type="application/json")
        assert res.status_code == 200, f"Action leave failed: {res.data}"

        # Verify balance reduction & status synchronization
        db.session.refresh(lv)
        db.session.refresh(balance)
        assert lv.status == "Approved", "Leave status not approved in DB"
        assert balance.used == 3, "Leave balance used count not updated"
        assert balance.remaining == 7, "Leave balance remaining count not recalculated"

        # Cleanup
        db.session.delete(lv)
        db.session.delete(balance)
        db.session.delete(dept)
        Notification.query.filter(Notification.user_id.in_([employee.id, manager.id, delegate.id])).delete()
        db.session.delete(employee)
        db.session.delete(manager)
        db.session.delete(delegate)
        db.session.delete(admin)
        db.session.commit()

        print("PASS: Leave Management Workflow")

if __name__ == "__main__":
    run_workflow()
