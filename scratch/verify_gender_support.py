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

class GenderSupportTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        # Create department
        self.dept = Department(name="HR", description="HR department")
        db.session.add(self.dept)
        db.session.commit()

        # Create Admin
        self.admin = User(
            employee_id="AD-01",
            email="admin@company.com",
            name="Admin User",
            role="Admin",
            password_hash="hashed",
            department_id=self.dept.id
        )
        db.session.add(self.admin)
        db.session.commit()

        self.admin_token = jwt.encode(
            {"user_id": self.admin.id, "role": "Admin", "exp": datetime.utcnow() + timedelta(hours=1)},
            self.app.config["JWT_SECRET_KEY"],
            algorithm="HS256"
        )

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_default_gender_and_api(self):
        # Create an employee via Admin endpoint
        payload = {
            "name": "Jane Doe",
            "email": "jane@company.com",
            "password": "Password@123",
            "department_id": self.dept.id,
            "gender": "Female"
        }
        res = self.client.post(
            "/api/employees/",
            headers={"Authorization": f"Bearer {self.admin_token}"},
            data=json.dumps(payload),
            content_type="application/json"
        )
        self.assertEqual(res.status_code, 201)
        data = json.loads(res.data)
        self.assertEqual(data["gender"], "Female")

        # Verify default gender is Male if not provided
        payload_default = {
            "name": "John Doe",
            "email": "john@company.com",
            "password": "Password@123",
            "department_id": self.dept.id
        }
        res_def = self.client.post(
            "/api/employees/",
            headers={"Authorization": f"Bearer {self.admin_token}"},
            data=json.dumps(payload_default),
            content_type="application/json"
        )
        self.assertEqual(res_def.status_code, 201)
        data_def = json.loads(res_def.data)
        self.assertEqual(data_def["gender"], "Male")

        # Update gender as admin
        update_payload = {
            "gender": "Female"
        }
        res_update = self.client.put(
            f"/api/employees/{data_def['id']}",
            headers={"Authorization": f"Bearer {self.admin_token}"},
            data=json.dumps(update_payload),
            content_type="application/json"
        )
        self.assertEqual(res_update.status_code, 200)
        data_updated = json.loads(res_update.data)
        self.assertEqual(data_updated["gender"], "Female")

        # Verify persistence in database
        db_user = User.query.get(data_def['id'])
        self.assertEqual(db_user.gender, "Female")

if __name__ == '__main__':
    unittest.main()
