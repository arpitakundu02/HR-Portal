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
from models import User, Leave, Attendance, Department
from config import Config

class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    JWT_SECRET_KEY = "test_secret_key"
    JWT_ALGORITHM = "HS256"

class UpcomingLeaveTestCase(unittest.TestCase):
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
        self.target = User(
            employee_id="EM-02",
            email="target@company.com",
            name="Target User",
            role="Employee",
            password_hash="hashed",
            department_id=self.dept.id
        )
        db.session.add_all([self.admin, self.employee, self.target])
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

    def get_upcoming_leave(self, token, user_id):
        # Fetch from List endpoint
        res = self.client.get("/api/employees/", headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        list_upcoming = None
        for emp in data["employees"]:
            if emp["id"] == user_id:
                list_upcoming = emp.get("upcoming_leave")

        # Fetch from Details endpoint
        res_detail = self.client.get(f"/api/employees/{user_id}", headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(res_detail.status_code, 200)
        data_detail = json.loads(res_detail.data)
        detail_upcoming = data_detail.get("upcoming_leave")

        # Basic assertion that list and detail matches
        self.assertEqual(list_upcoming, detail_upcoming, "List and details upcoming_leave payload mismatch!")
        return list_upcoming

    def test_upcoming_leave_rules(self):
        today = date.today()

        # 1. No future approved leave -> upcoming_leave = null
        res_admin = self.get_upcoming_leave(self.admin_token, self.target.id)
        res_emp = self.get_upcoming_leave(self.emp_token, self.target.id)
        self.assertIsNone(res_admin)
        self.assertIsNone(res_emp)

        # 2. Add one future approved leave -> nearest leave returned correctly
        leave_near = Leave(
            employee_id=self.target.id,
            leave_type="WFH",
            start_date=today + timedelta(days=3),
            end_date=today + timedelta(days=5),
            status="Approved",
            reason="Work on project from home"
        )
        db.session.add(leave_near)
        db.session.commit()

        # Verify correct return
        res = self.get_upcoming_leave(self.emp_token, self.target.id)
        self.assertIsNotNone(res)
        self.assertEqual(res["leave_type"], "WFH")
        self.assertEqual(res["days_until_start"], 3)
        self.assertEqual(res["start_date"], (today + timedelta(days=3)).isoformat())
        self.assertEqual(res["end_date"], (today + timedelta(days=5)).isoformat())
        
        # Verify reason is not exposed
        self.assertNotIn("reason", res)
        self.assertNotIn("responsibility_transfer_id", res)

        # 3. Add multiple future approved leaves -> only earliest leave returned
        leave_far = Leave(
            employee_id=self.target.id,
            leave_type="APL",
            start_date=today + timedelta(days=10),
            end_date=today + timedelta(days=12),
            status="Approved",
            reason="Family vacation"
        )
        db.session.add(leave_far)
        db.session.commit()

        # Verify only the nearest (3 days away) is returned
        res = self.get_upcoming_leave(self.emp_token, self.target.id)
        self.assertEqual(res["days_until_start"], 3)
        self.assertEqual(res["leave_type"], "WFH")

        # 4. Existing availability status logic remains unchanged
        # Target has no attendance today and no active leave today -> status = Unavailable
        res_detail = self.client.get(f"/api/employees/{self.target.id}", headers={"Authorization": f"Bearer {self.emp_token}"})
        data = json.loads(res_detail.data)
        self.assertEqual(data["availability_status"], "Unavailable")

        # Make Admin and Employee responses identical for upcoming_leave
        res_admin_val = self.get_upcoming_leave(self.admin_token, self.target.id)
        res_emp_val = self.get_upcoming_leave(self.emp_token, self.target.id)
        self.assertEqual(res_admin_val, res_emp_val)

if __name__ == '__main__':
    unittest.main()
