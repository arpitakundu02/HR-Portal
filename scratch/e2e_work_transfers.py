import os
import sys
import json
from datetime import datetime, timedelta, date

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))

from app import create_app
from extensions import db
from models import User, WorkTransferRequest, Task, Meeting, Notification, ApprovalRequest
from utils.approval_callbacks import ApprovalCallbackRegistry

def run_workflow():
    app = create_app()
    with app.app_context():
        # Setup test data
        employee = User(
            employee_id="TEST-WT-01",
            email="test_wt@company.com",
            name="WT Tester",
            role="Employee",
            password_hash="hashed"
        )
        manager = User(
            employee_id="TEST-WT-MGR",
            email="test_wt_mgr@company.com",
            name="WT Manager",
            role="Employee",
            password_hash="hashed"
        )
        delegate = User(
            employee_id="TEST-WT-DEL",
            email="test_wt_del@company.com",
            name="WT Delegate",
            role="Employee",
            password_hash="hashed"
        )
        db.session.add_all([employee, manager, delegate])
        db.session.commit()

        employee.manager_id = manager.id
        db.session.commit()

        # Create department for scope testing
        from models import Department
        dept = Department(name="WT Department", manager_id=manager.id)
        db.session.add(dept)
        db.session.commit()

        employee.department_id = dept.id
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
        del_token = jwt.encode(
            {"user_id": delegate.id, "role": "Employee", "exp": datetime.utcnow() + timedelta(hours=1)},
            app.config["JWT_SECRET_KEY"],
            algorithm="HS256"
        )

        client = app.test_client()

        # 1. Create Work Transfer Request
        start_date = date.today().isoformat()
        end_date = (date.today() + timedelta(days=5)).isoformat()
        res = client.post("/api/work-transfers/",
                          headers={"Authorization": f"Bearer {token}"},
                          data=json.dumps({
                              "delegate_to_id": delegate.id,
                              "start_date": start_date,
                              "end_date": end_date,
                              "transfer_tasks": True,
                              "transfer_approvals": True,
                              "transfer_meetings": True
                          }),
                          content_type="application/json")
        assert res.status_code == 201, f"WT creation failed: {res.data}"
        wt_data = json.loads(res.data)

        # Verify approval request was generated
        wtr = WorkTransferRequest.query.get(wt_data["id"])
        assert wtr.approval_request_id is not None, "WT ApprovalRequest not generated"

        # 2. Action Work Transfer Request (Approve)
        res_act = client.post(f"/api/approvals/{wtr.approval_request_id}/action",
                              headers={"Authorization": f"Bearer {mgr_token}"},
                              data=json.dumps({"status": "Approved", "comments": "Delegate verified"}),
                              content_type="application/json")
        assert res_act.status_code == 200, f"WT Approval failed: {res_act.data}"

        # 3. Create a task assigned to employee
        task = Task(
            title="WT Test Task",
            description="Work Delegation Task",
            employee_id=employee.id,
            status="Pending",
            assigned_by=manager.id
        )
        db.session.add(task)
        db.session.commit()

        # Verify delegated tasks visibility
        res_tasks = client.get("/api/tasks/", headers={"Authorization": f"Bearer {del_token}"})
        assert res_tasks.status_code == 200
        tasks_data = json.loads(res_tasks.data)
        task_ids = [t["id"] for t in tasks_data.get("tasks", [])]
        assert task.id in task_ids, "Delegate cannot view delegated tasks"

        # 4. Create a meeting owned by employee
        meeting = Meeting(
            title="WT Test Meeting",
            description="Work Delegation Meeting",
            department_id=dept.id,
            scheduled_at=datetime.utcnow() + timedelta(hours=2),
            created_by=employee.id
        )
        db.session.add(meeting)
        db.session.commit()

        # Verify delegated meetings visibility
        res_meetings = client.get("/api/meetings/", headers={"Authorization": f"Bearer {del_token}"})
        assert res_meetings.status_code == 200
        meetings_data = json.loads(res_meetings.data)
        meeting_ids = [m["id"] for m in meetings_data]
        assert meeting.id in meeting_ids, "Delegate cannot view delegated meetings"

        # Cleanup
        db.session.delete(task)
        db.session.delete(meeting)
        app_req = ApprovalRequest.query.get(wtr.approval_request_id)
        if app_req:
            db.session.delete(app_req)
        db.session.delete(wtr)
        db.session.delete(dept)
        Notification.query.filter(Notification.user_id.in_([employee.id, manager.id, delegate.id])).delete()
        db.session.delete(employee)
        db.session.delete(manager)
        db.session.delete(delegate)
        db.session.commit()

        print("PASS: Work Transfer Requests Workflow")

if __name__ == "__main__":
    run_workflow()
