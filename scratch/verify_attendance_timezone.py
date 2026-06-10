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
from models import User, Attendance, AttendanceAdjustment, Department
from config import Config

class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    JWT_SECRET_KEY = "test_secret_key"
    JWT_ALGORITHM = "HS256"

class AttendanceTimezoneTestCase(unittest.TestCase):
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
        self.employee = User(
            employee_id="EM-01",
            email="employee@company.com",
            name="Employee User",
            role="Employee",
            password_hash="hashed",
            department_id=self.dept.id
        )
        db.session.add(self.employee)
        db.session.commit()

        # Generate tokens
        self.emp_token = jwt.encode(
            {"user_id": self.employee.id, "role": "Employee", "exp": datetime.utcnow() + timedelta(hours=1)},
            self.app.config["JWT_SECRET_KEY"],
            algorithm="HS256"
        )

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_midnight_shift_flow(self):
        # 1. Simulate a check-in on the previous day (yesterday)
        from routes.attendance import _get_company_date
        today_date = _get_company_date()
        yesterday_date = today_date - timedelta(days=1)

        att = Attendance(
            employee_id=self.employee.id,
            date=yesterday_date,
            check_in=datetime.utcnow() - timedelta(hours=3),
            latitude=28.6139,
            longitude=77.2090
        )
        db.session.add(att)
        db.session.commit()

        # 2. Get status: should return checked_in for yesterday's shift since check_out is None
        res_status = self.client.get("/api/attendance/status", headers={"Authorization": f"Bearer {self.emp_token}"})
        self.assertEqual(res_status.status_code, 200)
        data_status = json.loads(res_status.data)
        self.assertEqual(data_status["status"], "checked_in")
        self.assertEqual(data_status["date"], yesterday_date.isoformat())

        # 3. Try checking in again today: should be blocked by active yesterday's shift
        office_lat = self.app.config.get("OFFICE_LATITUDE", 28.6139)
        office_lon = self.app.config.get("OFFICE_LONGITUDE", 77.2090)
        res_checkin = self.client.post("/api/attendance/checkin",
                                       headers={"Authorization": f"Bearer {self.emp_token}"},
                                       data=json.dumps({"latitude": office_lat, "longitude": office_lon}),
                                       content_type="application/json")
        self.assertEqual(res_checkin.status_code, 409)
        self.assertIn("active checked-in shift from yesterday", json.loads(res_checkin.data)["error"])

        # 4. Check out: should succeed and resolve yesterday's shift
        res_checkout = self.client.post("/api/attendance/checkout", headers={"Authorization": f"Bearer {self.emp_token}"})
        self.assertEqual(res_checkout.status_code, 200)
        data_checkout = json.loads(res_checkout.data)
        self.assertIn("Check-out recorded", data_checkout["message"])

        # Check DB that the record got checked out
        db_att = Attendance.query.filter_by(employee_id=self.employee.id, date=yesterday_date).first()
        self.assertIsNotNone(db_att.check_out)

        # 5. Get status again: should now be not_checked_in for today
        res_status2 = self.client.get("/api/attendance/status", headers={"Authorization": f"Bearer {self.emp_token}"})
        self.assertEqual(res_status2.status_code, 200)
        self.assertEqual(json.loads(res_status2.data)["status"], "not_checked_in")

    def test_regularization_month_limits(self):
        # We need to verify that monthly counts are calculated correctly relative to IST month boundaries.
        # We will insert 4 adjustments in the current calendar month
        from routes.attendance import _get_company_date
        today_date = _get_company_date()
        
        # 4 adjustments inside this month
        for i in range(4):
            adj = AttendanceAdjustment(
                employee_id=self.employee.id,
                date=today_date - timedelta(days=i + 1),
                check_in=datetime.utcnow() - timedelta(days=i + 1),
                check_out=datetime.utcnow() - timedelta(days=i + 1, hours=-8),
                reason="Regularization reason explanation",
                status="Approved",
                created_at=datetime.utcnow() - timedelta(minutes=i)
            )
            db.session.add(adj)
        db.session.commit()

        # Try submitting a 5th one: should return 429
        req_data = {
            "date": (today_date - timedelta(days=5)).isoformat(),
            "check_in": "09:00",
            "check_out": "17:00",
            "reason": "Forgot to check in again"
        }
        res = self.client.post("/api/attendance/regularization",
                               headers={"Authorization": f"Bearer {self.emp_token}"},
                               data=json.dumps(req_data),
                               content_type="application/json")
        self.assertEqual(res.status_code, 429)
        self.assertIn("Monthly regularization limit", json.loads(res.data)["error"])

if __name__ == '__main__':
    unittest.main()
