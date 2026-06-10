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
from models import User, Holiday
from config import Config

class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    JWT_SECRET_KEY = "test_secret_key"
    JWT_ALGORITHM = "HS256"

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

    def test_create_holiday_admin_only(self):
        # Employee should be forbidden
        res = self.client.post("/api/holidays",
                               headers={"Authorization": f"Bearer {self.emp_token}"},
                               data=json.dumps({"name": "New Year", "date": "2027-01-01", "description": "Holiday"}),
                               content_type="application/json")
        self.assertEqual(res.status_code, 403)

        # Admin should succeed
        res = self.client.post("/api/holidays",
                               headers={"Authorization": f"Bearer {self.admin_token}"},
                               data=json.dumps({"name": "New Year", "date": "2027-01-01", "description": "Holiday"}),
                               content_type="application/json")
        self.assertEqual(res.status_code, 201)
        data = json.loads(res.data)
        self.assertEqual(data["name"], "New Year")

    def test_duplicate_holiday_prevention(self):
        # Create first holiday
        self.client.post("/api/holidays",
                         headers={"Authorization": f"Bearer {self.admin_token}"},
                         data=json.dumps({"name": "Holiday A", "date": "2027-01-01", "description": "Day A"}),
                         content_type="application/json")

        # Try duplicate date
        res = self.client.post("/api/holidays",
                               headers={"Authorization": f"Bearer {self.admin_token}"},
                               data=json.dumps({"name": "Holiday B", "date": "2027-01-01", "description": "Day B"}),
                               content_type="application/json")
        self.assertEqual(res.status_code, 400)
        data = json.loads(res.data)
        self.assertIn("already scheduled on this date", data["error"])

    def test_upcoming_filter_and_sorting(self):
        # Insert one past and two future holidays
        past_date = (date.today() - timedelta(days=5)).isoformat()
        future_near = (date.today() + timedelta(days=2)).isoformat()
        future_far = (date.today() + timedelta(days=10)).isoformat()

        # Insert directly to db for setup
        h1 = Holiday(name="Past", date=datetime.strptime(past_date, "%Y-%m-%d").date())
        h2 = Holiday(name="Future Near", date=datetime.strptime(future_near, "%Y-%m-%d").date())
        h3 = Holiday(name="Future Far", date=datetime.strptime(future_far, "%Y-%m-%d").date())
        db.session.add_all([h1, h2, h3])
        db.session.commit()

        # Fetch only upcoming
        res = self.client.get("/api/holidays?upcoming=true",
                               headers={"Authorization": f"Bearer {self.emp_token}"})
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        
        # Filter for our test holidays to check presence and order
        names = [h["name"] for h in data if h["name"] in ["Past", "Future Near", "Future Far"]]
        self.assertNotIn("Past", names)
        self.assertEqual(names, ["Future Near", "Future Far"])

    def test_limit_parameter(self):
        future_1 = (date.today() + timedelta(days=2)).isoformat()
        future_2 = (date.today() + timedelta(days=5)).isoformat()
        future_3 = (date.today() + timedelta(days=10)).isoformat()

        # To prevent next year auto-population from interfering, we can query specifically or limit
        h1 = Holiday(name="F1", date=datetime.strptime(future_1, "%Y-%m-%d").date())
        h2 = Holiday(name="F2", date=datetime.strptime(future_2, "%Y-%m-%d").date())
        h3 = Holiday(name="F3", date=datetime.strptime(future_3, "%Y-%m-%d").date())
        db.session.add_all([h1, h2, h3])
        db.session.commit()

        # Fetch with limit=2
        res = self.client.get("/api/holidays?upcoming=true&limit=2",
                               headers={"Authorization": f"Bearer {self.emp_token}"})
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertEqual(len(data), 2)
        # Ensure they are sorted ascending (nearest first)
        self.assertTrue(datetime.strptime(data[0]["date"], "%Y-%m-%d").date() <= datetime.strptime(data[1]["date"], "%Y-%m-%d").date())

    def test_indian_holidays_auto_population(self):
        # Database has no holidays
        self.assertEqual(Holiday.query.count(), 0)

        # Trigger GET endpoint
        res = self.client.get("/api/holidays",
                              headers={"Authorization": f"Bearer {self.emp_token}"})
        self.assertEqual(res.status_code, 200)

        # Holidays should now exist in database
        self.assertGreater(Holiday.query.count(), 0)

if __name__ == '__main__':
    unittest.main()
