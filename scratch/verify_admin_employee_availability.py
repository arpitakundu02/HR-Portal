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

class AdminEmployeeAvailabilityTestCase(unittest.TestCase):
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

    def get_status(self, token, user_id):
        # Fetch from List endpoint
        res = self.client.get("/api/employees/", headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        list_status = None
        for emp in data["employees"]:
            if emp["id"] == user_id:
                list_status = emp.get("availability_status")

        # Fetch from Details endpoint
        res_detail = self.client.get(f"/api/employees/{user_id}", headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(res_detail.status_code, 200)
        data_detail = json.loads(res_detail.data)
        detail_status = data_detail.get("availability_status")

        self.assertEqual(list_status, detail_status, "List and details endpoint status mismatch!")
        return list_status

    def test_all_availability_cases(self):
        today = date.today()

        # Case 1: No attendance/no leave -> Unavailable
        admin_status = self.get_status(self.admin_token, self.target.id)
        emp_status = self.get_status(self.emp_token, self.target.id)
        self.assertEqual(admin_status, "Unavailable")
        self.assertEqual(emp_status, "Unavailable")

        # Case 2: Checked-in only -> Present
        att = Attendance(employee_id=self.target.id, date=today, check_in=datetime.now())
        db.session.add(att)
        db.session.commit()
        admin_status = self.get_status(self.admin_token, self.target.id)
        emp_status = self.get_status(self.emp_token, self.target.id)
        self.assertEqual(admin_status, "Present")
        self.assertEqual(emp_status, "Present")

        # Case 3: Checked-out -> Unavailable
        att.check_out = datetime.now() + timedelta(hours=8)
        db.session.commit()
        admin_status = self.get_status(self.admin_token, self.target.id)
        emp_status = self.get_status(self.emp_token, self.target.id)
        self.assertEqual(admin_status, "Unavailable")
        self.assertEqual(emp_status, "Unavailable")

        # Case 4: Approved WFH leave today -> Work From Home (leave overrides attendance)
        leave_wfh = Leave(
            employee_id=self.target.id,
            leave_type="WFH",
            start_date=today,
            end_date=today,
            status="Approved"
        )
        db.session.add(leave_wfh)
        db.session.commit()
        admin_status = self.get_status(self.admin_token, self.target.id)
        emp_status = self.get_status(self.emp_token, self.target.id)
        self.assertEqual(admin_status, "Work From Home")
        self.assertEqual(emp_status, "Work From Home")

        # Case 5: Approved APL leave today -> On Leave (leave overrides attendance)
        leave_wfh.status = "Rejected"
        leave_apl = Leave(
            employee_id=self.target.id,
            leave_type="APL",
            start_date=today,
            end_date=today,
            status="Approved"
        )
        db.session.add(leave_apl)
        db.session.commit()
        admin_status = self.get_status(self.admin_token, self.target.id)
        emp_status = self.get_status(self.emp_token, self.target.id)
        self.assertEqual(admin_status, "On Leave")
        self.assertEqual(emp_status, "On Leave")

if __name__ == '__main__':
    unittest.main()
