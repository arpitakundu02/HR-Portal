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

class BioExperienceTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        # Create departments
        self.dept_eng = Department(name="Engineering", description="Devs")
        db.session.add(self.dept_eng)
        db.session.commit()

        # Create test users (admin, employee, line manager)
        self.admin = User(
            employee_id="AD-01",
            email="admin@company.com",
            name="Admin User",
            role="Admin",
            password_hash="hashed",
            department_id=self.dept_eng.id,
            is_line_manager=False
        )
        self.manager = User(
            employee_id="LM-01",
            email="manager@company.com",
            name="Manager User",
            role="Employee",
            password_hash="hashed",
            department_id=self.dept_eng.id,
            is_line_manager=True
        )
        db.session.add_all([self.admin, self.manager])
        db.session.commit()

        self.employee = User(
            employee_id="EM-01",
            email="emp1@company.com",
            name="Employee One",
            role="Employee",
            password_hash="hashed",
            department_id=self.dept_eng.id,
            manager_id=self.manager.id,
            is_line_manager=False
        )
        db.session.add(self.employee)
        db.session.commit()

        # Generate tokens
        self.admin_token = jwt.encode(
            {"user_id": self.admin.id, "role": "Admin", "exp": datetime.utcnow() + timedelta(hours=1)},
            self.app.config["JWT_SECRET_KEY"],
            algorithm="HS256"
        )
        self.mgr_token = jwt.encode(
            {"user_id": self.manager.id, "role": "Employee", "exp": datetime.utcnow() + timedelta(hours=1)},
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

    def test_update_bio_and_experience_success(self):
        # Update as self
        payload = {
            "bio": "This is my custom bio. It can be of any length as per the modified requirements.",
            "experience_summary": "5 years of experience in Python and Flask."
        }
        res = self.client.put(
            f"/api/employees/{self.employee.id}",
            headers={"Authorization": f"Bearer {self.emp_token}"},
            data=json.dumps(payload),
            content_type="application/json"
        )
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertEqual(data["bio"], payload["bio"])
        self.assertEqual(data["experience_summary"], payload["experience_summary"])

        # Verify database persistence
        db_user = User.query.get(self.employee.id)
        self.assertEqual(db_user.bio, payload["bio"])
        self.assertEqual(db_user.experience_summary, payload["experience_summary"])

    def test_experience_summary_length_validation(self):
        # Over 5000 characters experience summary should fail
        payload = {
            "experience_summary": "A" * 5001
        }
        res = self.client.put(
            f"/api/employees/{self.employee.id}",
            headers={"Authorization": f"Bearer {self.emp_token}"},
            data=json.dumps(payload),
            content_type="application/json"
        )
        self.assertEqual(res.status_code, 422)
        data = json.loads(res.data)
        self.assertEqual(data["error"], "Experience summary must be under 5000 characters.")

    def test_visibility_rules(self):
        # Set bio and experience
        db_user = User.query.get(self.employee.id)
        db_user.bio = "Confidential Bio"
        db_user.experience_summary = "Confidential Exp"
        db.session.commit()

        # 1. Self can view
        res = self.client.get(f"/api/employees/{self.employee.id}", headers={"Authorization": f"Bearer {self.emp_token}"})
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertEqual(data["bio"], "Confidential Bio")
        self.assertEqual(data["experience_summary"], "Confidential Exp")

        # 2. Admin can view
        res = self.client.get(f"/api/employees/{self.employee.id}", headers={"Authorization": f"Bearer {self.admin_token}"})
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertEqual(data["bio"], "Confidential Bio")
        self.assertEqual(data["experience_summary"], "Confidential Exp")

        # 3. Line Manager can view
        res = self.client.get(f"/api/employees/{self.employee.id}", headers={"Authorization": f"Bearer {self.mgr_token}"})
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertEqual(data["bio"], "Confidential Bio")
        self.assertEqual(data["experience_summary"], "Confidential Exp")

    def test_dashboard_details_endpoint_visibility(self):
        # Set bio and experience
        db_user = User.query.get(self.employee.id)
        db_user.bio = "Dashboard Bio"
        db_user.experience_summary = "Dashboard Exp"
        db.session.commit()

        # 1. Employee themselves can view dashboard details
        res = self.client.get(f"/api/employees/{self.employee.id}/dashboard-details", headers={"Authorization": f"Bearer {self.emp_token}"})
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertEqual(data["profile"]["bio"], "Dashboard Bio")
        self.assertEqual(data["profile"]["experience_summary"], "Dashboard Exp")

        # 2. Line Manager can view dashboard details
        res = self.client.get(f"/api/employees/{self.employee.id}/dashboard-details", headers={"Authorization": f"Bearer {self.mgr_token}"})
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertEqual(data["profile"]["bio"], "Dashboard Bio")
        self.assertEqual(data["profile"]["experience_summary"], "Dashboard Exp")

        # 3. Admin can view dashboard details
        res = self.client.get(f"/api/employees/{self.employee.id}/dashboard-details", headers={"Authorization": f"Bearer {self.admin_token}"})
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertEqual(data["profile"]["bio"], "Dashboard Bio")
        self.assertEqual(data["profile"]["experience_summary"], "Dashboard Exp")

if __name__ == '__main__':
    unittest.main()
