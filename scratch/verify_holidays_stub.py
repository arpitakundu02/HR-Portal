import os
import sys
import unittest
from datetime import datetime, timedelta

# Adjust path to import from backend
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))

from app import create_app
from extensions import db
from models import User, Holiday
from config import Config

class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    JWT_SECRET_KEY = "test_secret_key"

class HolidaysTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        # Create test users
        self.admin = User(
            employee_id="AD-01",
            email="admin@company.com",
            name="Admin User",
            role="Admin",
            password_hash="hashed"
        )
        self.employee = User(
            employee_id="EM-01",
            email="employee@company.com",
            name="Employee User",
            role="Employee",
            password_hash="hashed"
        )
        db.session.add(self.admin)
        db.session.add(self.employee)
        db.session.commit()

        # Generate test JWT tokens
        from flask_jwt_extended import create_access_token
        # Wait, the app uses custom jwt_required or flask_jwt_extended? Let's check decorators.py
        # Actually, let's verify what decorators import.
        # Oh, let's look at a verify script in scratch to see how tokens are generated.

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

if __name__ == '__main__':
    unittest.main()
