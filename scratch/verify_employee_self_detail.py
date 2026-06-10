import os
import sys
import unittest
import json
from datetime import datetime, timedelta
import jwt

# Adjust path to import from backend
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))

from app import create_app
from extensions import db
from models import User, Department
from config import Config

class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    JWT_SECRET_KEY = "test_secret_key"
    JWT_ALGORITHM = "HS256"

class EmployeeSelfDetailTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        # Create departments
        self.dept_eng = Department(name="Engineering", description="Devs")
        self.dept_hr = Department(name="HR", description="HR team")
        db.session.add_all([self.dept_eng, self.dept_hr])
        db.session.commit()

        # Create test users
        self.admin = User(
            employee_id="AD-01",
            email="admin@company.com",
            name="Admin User",
            role="Admin",
            password_hash="hashed",
            department_id=self.dept_hr.id,
            salary=100000,
            aadhar_number="123456789012"
        )
        self.employee1 = User(
            employee_id="EM-01",
            email="emp1@company.com",
            name="Employee One",
            role="Employee",
            password_hash="hashed",
            department_id=self.dept_eng.id,
            salary=50000,
            aadhar_number="987654321098"
        )
        self.employee2 = User(
            employee_id="EM-02",
            email="emp2@company.com",
            name="Employee Two",
            role="Employee",
            password_hash="hashed",
            department_id=self.dept_eng.id,
            salary=60000,
            aadhar_number="111122223333"
        )
        self.employee_other_dept = User(
            employee_id="EM-03",
            email="emp3@company.com",
            name="Employee Other Dept",
            role="Employee",
            password_hash="hashed",
            department_id=self.dept_hr.id,
            salary=70000,
            aadhar_number="444455556666"
        )
        db.session.add_all([self.admin, self.employee1, self.employee2, self.employee_other_dept])
        db.session.commit()

        # Generate tokens
        self.admin_token = jwt.encode(
            {"user_id": self.admin.id, "role": "Admin", "exp": datetime.utcnow() + timedelta(hours=1)},
            self.app.config["JWT_SECRET_KEY"],
            algorithm="HS256"
        )
        self.emp1_token = jwt.encode(
            {"user_id": self.employee1.id, "role": "Employee", "exp": datetime.utcnow() + timedelta(hours=1)},
            self.app.config["JWT_SECRET_KEY"],
            algorithm="HS256"
        )

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_admin_can_view_any_sensitive(self):
        # Admin requests employee1
        res = self.client.get(f"/api/employees/{self.employee1.id}", headers={"Authorization": f"Bearer {self.admin_token}"})
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertIn("salary", data)
        self.assertIn("aadhar_number", data)
        self.assertEqual(data["salary"], 50000.0)
        self.assertEqual(data["aadhar_number"], "987654321098")

    def test_employee_can_view_own_sensitive(self):
        # Employee1 requests employee1
        res = self.client.get(f"/api/employees/{self.employee1.id}", headers={"Authorization": f"Bearer {self.emp1_token}"})
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertIn("salary", data)
        self.assertIn("aadhar_number", data)
        self.assertEqual(data["salary"], 50000.0)
        self.assertEqual(data["aadhar_number"], "987654321098")

    def test_employee_cannot_view_other_sensitive(self):
        # Employee1 requests employee2 (same department)
        res = self.client.get(f"/api/employees/{self.employee2.id}", headers={"Authorization": f"Bearer {self.emp1_token}"})
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        # Should not have sensitive fields
        self.assertNotIn("salary", data)
        self.assertNotIn("aadhar_number", data)
        # Should see basic fields
        self.assertEqual(data["name"], "Employee Two")
        self.assertEqual(data["email"], "emp2@company.com")

    def test_employee_cannot_view_different_dept_at_all(self):
        # Employee1 requests employee_other_dept (different department)
        res = self.client.get(f"/api/employees/{self.employee_other_dept.id}", headers={"Authorization": f"Bearer {self.emp1_token}"})
        self.assertEqual(res.status_code, 403)
        data = json.loads(res.data)
        self.assertIn("error", data)
        self.assertEqual(data["error"], "Access denied.")

if __name__ == '__main__':
    unittest.main()
