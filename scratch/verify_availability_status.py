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
from models import User, Holiday, Leave, Attendance, Department
from config import Config

class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    JWT_SECRET_KEY = "test_secret_key"
    JWT_ALGORITHM = "HS256"

class AvailabilityStatusTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        # Create department
        self.dept = Department(name="Engineering", description="Devs")
        db.session.add(self.dept)
        db.session.commit()

        # Create test users
        self.admin = User(
            employee_id="AD-01",
            email="admin@company.com",
            name="Admin User",
            role="Admin",
            password_hash="hashed",
            department_id=self.dept.id
        )
        self.employee = User(
            employee_id="EM-01",
            email="employee@company.com",
            name="Employee User",
            role="Employee",
            password_hash="hashed",
            department_id=self.dept.id
        )
        self.peer = User(
            employee_id="EM-02",
            email="peer@company.com",
            name="Peer User",
            role="Employee",
            password_hash="hashed",
            department_id=self.dept.id
        )
        db.session.add_all([self.admin, self.employee, self.peer])
        db.session.commit()

        # Generate tokens
        self.admin_token = jwt.encode(
            {"user_id": self.admin.id, "role": "Admin", "exp": datetime.utcnow() + timedelta(hours=1)},
            self.app.config["JWT_SECRET_KEY"],
            algorithm="HS256"
        )
        self.emp_token = jwt.encode(
            {"user_id": self.employee.id, "role": "Employee", "exp": datetime.utcnow() + timedelta(hours=1)},
            self.app.config["JWT_SECRET_KEY"],
            algorithm="HS256"
        )

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def get_peer_status(self, peer_id):
        res = self.client.get("/api/employees/", headers={"Authorization": f"Bearer {self.emp_token}"})
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        for emp in data["employees"]:
            if emp["id"] == peer_id:
                return emp.get("availability_status")
        return None

    def test_status_cases(self):
        today = date.today()

        # 1. No attendance and no leave -> Unavailable
        status = self.get_peer_status(self.peer.id)
        self.assertEqual(status, "Unavailable")

        # 2. Employee checked in only -> Present
        att = Attendance(employee_id=self.peer.id, date=today, check_in=datetime.now())
        db.session.add(att)
        db.session.commit()
        status = self.get_peer_status(self.peer.id)
        self.assertEqual(status, "Present")

        # 3. Employee checked in and checked out -> Unavailable
        att.check_out = datetime.now() + timedelta(hours=8)
        db.session.commit()
        status = self.get_peer_status(self.peer.id)
        self.assertEqual(status, "Unavailable")

        # 4. Employee with approved WFH leave -> Work From Home
        # Even if attendance checked in/out exists, leave should override it
        leave_wfh = Leave(
            employee_id=self.peer.id,
            leave_type="WFH",
            start_date=today,
            end_date=today,
            status="Approved"
        )
        db.session.add(leave_wfh)
        db.session.commit()
        status = self.get_peer_status(self.peer.id)
        self.assertEqual(status, "Work From Home")

        # 5. Employee with approved APL leave -> On Leave
        leave_wfh.status = "Rejected" # reject previous
        leave_apl = Leave(
            employee_id=self.peer.id,
            leave_type="APL",
            start_date=today,
            end_date=today,
            status="Approved"
        )
        db.session.add(leave_apl)
        db.session.commit()
        status = self.get_peer_status(self.peer.id)
        self.assertEqual(status, "On Leave")

    def test_admin_and_employee_views(self):
        # Admin gets full profiles which don't have availability_status computed at the list level (or have it based on logic)
        res = self.client.get("/api/employees/", headers={"Authorization": f"Bearer {self.admin_token}"})
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        # Admin view should also receive availability_status
        for emp in data["employees"]:
            self.assertIn("availability_status", emp)

if __name__ == '__main__':
    unittest.main()
