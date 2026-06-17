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
from models import User, Department, Leave, LeaveBalance
from config import Config

class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    JWT_SECRET_KEY = "test_secret_key"
    JWT_ALGORITHM = "HS256"

class LeaveEntitlementRulesTestCase(unittest.TestCase):
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

        # Create Admin
        self.admin = User(
            employee_id="AD-01",
            email="admin@company.com",
            name="Admin User",
            role="Admin",
            password_hash="hashed",
            department_id=self.dept.id
        )
        # Create Female Employee
        self.female_emp = User(
            employee_id="EM-F",
            email="female@company.com",
            name="Simran Kaur",
            role="Employee",
            password_hash="hashed",
            department_id=self.dept.id,
            gender="Female"
        )
        # Create Male Employee
        self.male_emp = User(
            employee_id="EM-M",
            email="male@company.com",
            name="Rohan Sharma",
            role="Employee",
            password_hash="hashed",
            department_id=self.dept.id,
            gender="Male"
        )
        db.session.add_all([self.admin, self.female_emp, self.male_emp])
        db.session.commit()

        # Create Leave Balances with default rules
        self.female_apl_bal = LeaveBalance(employee_id=self.female_emp.id, leave_type="APL", allocated=20, used=0, remaining=20)
        self.female_wfh_bal = LeaveBalance(employee_id=self.female_emp.id, leave_type="WFH", allocated=5, used=0, remaining=5)
        
        self.male_apl_bal = LeaveBalance(employee_id=self.male_emp.id, leave_type="APL", allocated=20, used=0, remaining=20)
        self.male_wfh_bal = LeaveBalance(employee_id=self.male_emp.id, leave_type="WFH", allocated=4, used=0, remaining=4)

        db.session.add_all([self.female_apl_bal, self.female_wfh_bal, self.male_apl_bal, self.male_wfh_bal])
        db.session.commit()

        # Generate tokens
        self.admin_token = jwt.encode(
            {"user_id": self.admin.id, "role": "Admin", "exp": datetime.utcnow() + timedelta(hours=1)},
            self.app.config["JWT_SECRET_KEY"],
            algorithm="HS256"
        )
        self.female_token = jwt.encode(
            {"user_id": self.female_emp.id, "role": "Employee", "exp": datetime.utcnow() + timedelta(hours=1)},
            self.app.config["JWT_SECRET_KEY"],
            algorithm="HS256"
        )
        self.male_token = jwt.encode(
            {"user_id": self.male_emp.id, "role": "Employee", "exp": datetime.utcnow() + timedelta(hours=1)},
            self.app.config["JWT_SECRET_KEY"],
            algorithm="HS256"
        )

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_apl_non_blocking_and_negative_balance(self):
        # Rohan submits APL request of 18 days
        l1 = Leave(
            employee_id=self.male_emp.id,
            leave_type="APL",
            start_date=date(2025, 6, 1),
            end_date=date(2025, 6, 18), # 18 days
            reason="Vacation",
            status="Pending",
            responsibility_transfer_id=self.female_emp.id
        )
        # Rohan submits another APL request of 3 days (Total = 21, exceeds yearly limit of 20)
        l2 = Leave(
            employee_id=self.male_emp.id,
            leave_type="APL",
            start_date=date(2025, 8, 1),
            end_date=date(2025, 8, 3), # 3 days
            reason="Personal work",
            status="Pending",
            responsibility_transfer_id=self.female_emp.id
        )
        db.session.add_all([l1, l2])
        db.session.commit()

        # Approve first APL request (18 days)
        res1 = self.client.post(
            f"/api/leaves/requests/{l1.id}/action",
            headers={"Authorization": f"Bearer {self.admin_token}"},
            data=json.dumps({"status": "Approved"}),
            content_type="application/json"
        )
        self.assertEqual(res1.status_code, 200)

        # Approve second APL request (3 days, exceeds 20 limit)
        # Should be approved successfully instead of blocked
        res2 = self.client.post(
            f"/api/leaves/requests/{l2.id}/action",
            headers={"Authorization": f"Bearer {self.admin_token}"},
            data=json.dumps({"status": "Approved"}),
            content_type="application/json"
        )
        self.assertEqual(res2.status_code, 200)

        # Check balance in database
        balance = LeaveBalance.query.filter_by(employee_id=self.male_emp.id, leave_type="APL").first()
        self.assertEqual(balance.allocated, 20)
        self.assertEqual(balance.used, 21)
        self.assertEqual(balance.remaining, -1) # Negative balance allowed!
        print(f"[✓] Verified APL balance can go negative: remaining = {balance.remaining}")

    def test_wfh_non_blocking_and_negative_balance(self):
        # 1. Male employee: WFH allocation is 4
        # Add 3 approved WFH days in August 2025
        l_male_approved = Leave(
            employee_id=self.male_emp.id,
            leave_type="WFH",
            start_date=date(2025, 8, 1),
            end_date=date(2025, 8, 3), # 3 days
            reason="WFH",
            status="Approved",
            responsibility_transfer_id=self.female_emp.id
        )
        db.session.add(l_male_approved)
        # Recalculate balance for approved leave
        self.male_wfh_bal.used = 3
        self.male_wfh_bal.recalculate()
        db.session.commit()

        # Rohan Sharma submits a 2-day WFH request (taking him to 5 total, exceeding male entitlement limit of 4)
        # Submission should be allowed successfully!
        payload = {
            "leave_type": "WFH",
            "start_date": "2025-08-10",
            "end_date": "2025-08-11", # 2 days
            "reason": "WFH",
            "responsibility_transfer_id": self.female_emp.id
        }
        res1 = self.client.post(
            "/api/leaves/apply",
            headers={"Authorization": f"Bearer {self.male_token}"},
            data=json.dumps(payload),
            content_type="application/json"
        )
        self.assertEqual(res1.status_code, 201)
        leave_id = json.loads(res1.data)["id"]

        # Admin approves the request
        res_approve = self.client.post(
            f"/api/leaves/requests/{leave_id}/action",
            headers={"Authorization": f"Bearer {self.admin_token}"},
            data=json.dumps({"status": "Approved"}),
            content_type="application/json"
        )
        self.assertEqual(res_approve.status_code, 200)

        # Check male balance in database
        balance = LeaveBalance.query.filter_by(employee_id=self.male_emp.id, leave_type="WFH").first()
        self.assertEqual(balance.allocated, 4)
        self.assertEqual(balance.used, 5)
        self.assertEqual(balance.remaining, -1) # Negative balance allowed!
        print(f"[✓] Verified Male WFH balance can go negative: remaining = {balance.remaining}")

        # 2. Female employee: WFH allocation is 5
        # Add 5 approved WFH days in August 2025
        l_female_approved = Leave(
            employee_id=self.female_emp.id,
            leave_type="WFH",
            start_date=date(2025, 8, 1),
            end_date=date(2025, 8, 5), # 5 days
            reason="WFH",
            status="Approved",
            responsibility_transfer_id=self.male_emp.id
        )
        db.session.add(l_female_approved)
        self.female_wfh_bal.used = 5
        self.female_wfh_bal.recalculate()
        db.session.commit()

        # Simran Kaur submits a 2-day WFH request (taking her to 7 total, exceeding female entitlement limit of 5)
        # Submission should be allowed successfully!
        payload_female = {
            "leave_type": "WFH",
            "start_date": "2025-08-10",
            "end_date": "2025-08-11", # 2 days
            "reason": "WFH",
            "responsibility_transfer_id": self.male_emp.id
        }
        res2 = self.client.post(
            "/api/leaves/apply",
            headers={"Authorization": f"Bearer {self.female_token}"},
            data=json.dumps(payload_female),
            content_type="application/json"
        )
        self.assertEqual(res2.status_code, 201)
        leave_id_f = json.loads(res2.data)["id"]

        # Admin approves the request
        res_approve_f = self.client.post(
            f"/api/leaves/requests/{leave_id_f}/action",
            headers={"Authorization": f"Bearer {self.admin_token}"},
            data=json.dumps({"status": "Approved"}),
            content_type="application/json"
        )
        self.assertEqual(res_approve_f.status_code, 200)

        # Check female balance in database
        balance_f = LeaveBalance.query.filter_by(employee_id=self.female_emp.id, leave_type="WFH").first()
        self.assertEqual(balance_f.allocated, 5)
        self.assertEqual(balance_f.used, 7)
        self.assertEqual(balance_f.remaining, -2) # Negative balance allowed!
        print(f"[✓] Verified Female WFH balance can go negative: remaining = {balance_f.remaining}")

if __name__ == '__main__':
    unittest.main()
