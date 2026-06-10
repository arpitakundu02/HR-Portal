import os
import sys
import unittest
import json
from datetime import datetime, timedelta, date, timezone
import jwt

# Adjust path to import from backend
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))

from app import create_app
from extensions import db
from models import User, Meeting, Department
from config import Config

class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    JWT_SECRET_KEY = "test_secret_key"
    JWT_ALGORITHM = "HS256"

class MeetingsTimezoneTestCase(unittest.TestCase):
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
        db.session.add(self.admin)
        db.session.commit()

        # Generate token
        self.admin_token = jwt.encode(
            {"user_id": self.admin.id, "role": "Admin", "exp": datetime.utcnow() + timedelta(hours=1)},
            self.app.config["JWT_SECRET_KEY"],
            algorithm="HS256"
        )

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_timezone_conversion_and_api(self):
        # 1. Create a meeting at 2:00 PM IST (14:00)
        # 2:00 PM IST is 8:30 AM UTC
        meeting_data = {
            "title": "Strategy Sync",
            "description": "Weekly sync",
            "scheduled_at": "2026-06-20T14:00:00",  # Naive local time (IST)
            "duration_minutes": 60,
            "link": "https://meet.google.com/abc"
        }

        res = self.client.post("/api/meetings/",
                               headers={"Authorization": f"Bearer {self.admin_token}"},
                               data=json.dumps(meeting_data),
                               content_type="application/json")
        self.assertEqual(res.status_code, 201)
        data = json.loads(res.data)

        # 2. Check API returns UTC ISO string with Z suffix
        self.assertEqual(data["scheduled_at"], "2026-06-20T08:30:00Z")

        # 3. Check exact value stored in SQLite (should be naive UTC datetime)
        meeting = Meeting.query.get(data["id"])
        self.assertEqual(meeting.scheduled_at, datetime(2026, 6, 20, 8, 30, 0))

    def test_upcoming_meetings_filter(self):
        # Insert a meeting in the past and one in the future (relative to UTC now)
        # Note: Meeting.scheduled_at is stored in UTC
        past_meeting = Meeting(
            title="Past Meeting",
            scheduled_at=datetime.utcnow() - timedelta(hours=2),
            duration_minutes=30,
            created_by=self.admin.id
        )
        future_meeting = Meeting(
            title="Future Meeting",
            scheduled_at=datetime.utcnow() + timedelta(hours=2),
            duration_minutes=30,
            created_by=self.admin.id
        )
        db.session.add_all([past_meeting, future_meeting])
        db.session.commit()

        # Call API list with upcoming=true
        res = self.client.get("/api/meetings/?upcoming=true",
                               headers={"Authorization": f"Bearer {self.admin_token}"})
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)

        # Should only return the future one
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["title"], "Future Meeting")
        self.assertTrue(data[0]["scheduled_at"].endswith("Z"))

if __name__ == '__main__':
    unittest.main()
