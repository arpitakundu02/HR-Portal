import os
import sys
import unittest
import json
from datetime import datetime, timedelta, date
import jwt

# Adjust path to import from backend
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))

from app import create_app
from extensions import db
from models import User, WorkTransferRequest, Task, Meeting, Notification, ApprovalRequest
from utils.approval_callbacks import ApprovalCallbackRegistry
from config import Config

class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    JWT_SECRET_KEY = "test_secret_key"
    JWT_ALGORITHM = "HS256"

class WorkTransfersTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        # Create test users (Manager, Requester, Delegate)
        self.manager = User(
            employee_id="MGR-01",
            email="manager@company.com",
            name="Manager User",
            role="Employee",
            password_hash="hashed"
        )
        self.requester = User(
            employee_id="REQ-01",
            email="requester@company.com",
            name="Requester User",
            role="Employee",
            password_hash="hashed"
        )
        self.delegate = User(
            employee_id="DEL-01",
            email="delegate@company.com",
            name="Delegate User",
            role="Employee",
            password_hash="hashed"
        )
        db.session.add_all([self.manager, self.requester, self.delegate])
        db.session.commit()

        # Create department
        from models import Department
        self.dept = Department(name="Engineering", manager_id=self.manager.id)
        db.session.add(self.dept)
        db.session.commit()

        # Setup reporting line and department membership
        self.requester.manager_id = self.manager.id
        self.requester.department_id = self.dept.id
        db.session.commit()

        # Generate JWT token for requester
        self.req_token = jwt.encode(
            {"user_id": self.requester.id, "role": "Employee", "exp": datetime.utcnow() + timedelta(hours=1)},
            self.app.config["JWT_SECRET_KEY"],
            algorithm="HS256"
        )
        self.mgr_token = jwt.encode(
            {"user_id": self.manager.id, "role": "Manager", "exp": datetime.utcnow() + timedelta(hours=1)},
            self.app.config["JWT_SECRET_KEY"],
            algorithm="HS256"
        )
        self.del_token = jwt.encode(
            {"user_id": self.delegate.id, "role": "Employee", "exp": datetime.utcnow() + timedelta(hours=1)},
            self.app.config["JWT_SECRET_KEY"],
            algorithm="HS256"
        )

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_work_transfer_creation_and_approval_routing(self):
        # 1. Create a work transfer request via POST endpoint
        start_date = date.today().isoformat()
        end_date = (date.today() + timedelta(days=5)).isoformat()
        res = self.client.post("/api/work-transfers/",
                               headers={"Authorization": f"Bearer {self.req_token}"},
                               data=json.dumps({
                                   "delegate_to_id": self.delegate.id,
                                   "start_date": start_date,
                                   "end_date": end_date,
                                   "transfer_tasks": True,
                                   "transfer_approvals": True,
                                   "transfer_meetings": True
                               }),
                               content_type="application/json")
        self.assertEqual(res.status_code, 201)
        data = json.loads(res.data)
        self.assertEqual(data["status"], "Pending")

        # Verify an approval request was created automatically
        wtr_id = data["id"]
        wtr = WorkTransferRequest.query.get(wtr_id)
        self.assertIsNotNone(wtr.approval_request_id)

        # 2. Verify notifications generated for delegate & manager
        notifs = Notification.query.all()
        # Should have at least notified delegate or manager
        self.assertTrue(len(notifs) >= 1)

        # 3. Approve using the Approval Engine callback handler (simulate manager approval)
        app_req = ApprovalRequest.query.get(wtr.approval_request_id)
        app_req.status = "Approved"
        ApprovalCallbackRegistry.execute("WorkTransfer", wtr.id, "Approved", db.session)
        db.session.commit()

        # Check status is now Approved
        db.session.refresh(wtr)
        self.assertEqual(wtr.status, "Approved")

        # 4. Check routing overrides during active delegation
        # Create a task assigned to requester
        task = Task(
            title="Important Work",
            description="Complete ASAP",
            employee_id=self.requester.id,
            status="Pending",
            assigned_by=self.manager.id
        )
        db.session.add(task)
        db.session.commit()

        # Fetch tasks as delegate - should see the delegated task
        res_tasks = self.client.get("/api/tasks/", headers={"Authorization": f"Bearer {self.del_token}"})
        self.assertEqual(res_tasks.status_code, 200)
        tasks_data = json.loads(res_tasks.data)
        task_ids = [t["id"] for t in tasks_data.get("tasks", [])]
        self.assertIn(task.id, task_ids)

        # Create a meeting owned by requester
        meeting = Meeting(
            title="Department Catchup",
            description="Weekly sync",
            department_id=self.dept.id,
            scheduled_at=datetime.utcnow() + timedelta(hours=2),
            created_by=self.requester.id
        )
        db.session.add(meeting)
        db.session.commit()

        # Fetch meetings as delegate - should see the delegated meeting
        res_meetings = self.client.get("/api/meetings/", headers={"Authorization": f"Bearer {self.del_token}"})
        self.assertEqual(res_meetings.status_code, 200)
        meetings_data = json.loads(res_meetings.data)
        meeting_ids = [m["id"] for m in meetings_data]
        self.assertIn(meeting.id, meeting_ids)

if __name__ == '__main__':
    unittest.main()
