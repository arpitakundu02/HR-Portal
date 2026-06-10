import sys
import os
from datetime import datetime, date, timedelta
import jwt

# Add backend to python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))

from app import create_app
from extensions import db
from models import User, Attendance, AttendanceAdjustment

app = create_app()

def get_next_day_date_string(date_val):
    # Matches JavaScript frontend date increment helper logic
    d = datetime.strptime(date_val, "%Y-%m-%d")
    d += timedelta(days=1)
    return d.strftime("%Y-%m-%d")

def build_payload(date_val, check_in_time, check_out_time, reason):
    # Replicates JS frontend payload construction logic
    check_in = f"{date_val}T{check_in_time}:00" if check_in_time else None
    
    check_out_date = date_val
    if check_in_time and check_out_time and check_out_time <= check_in_time:
        check_out_date = get_next_day_date_string(date_val)
        
    check_out = f"{check_out_date}T{check_out_time}:00" if check_out_time else None
    
    return {
        "date": date_val,
        "check_in": check_in,
        "check_out": check_out,
        "reason": reason
    }

def run_tests():
    print("=============================================================")
    print("OVERNIGHT REGULARIZATION VERIFICATION SUITE")
    print("=============================================================")
    
    with app.app_context():
        # Setup test employee
        employee_email = "overnight.test@company.com"
        emp = User.query.filter_by(email=employee_email).first()
        if not emp:
            emp = User(
                employee_id="OV-TEST",
                email=employee_email,
                password_hash="fakehash",
                role="Employee",
                name="Overnight Test Employee"
            )
            db.session.add(emp)
            db.session.commit()
            print(f"[✓] Created test employee with ID {emp.id}")

        # Setup test admin
        admin_email = "admin@hrportal.com"
        admin = User.query.filter_by(email=admin_email).first()
        if not admin:
            admin = User(
                employee_id="HR-ADMIN",
                email=admin_email,
                password_hash="fakehash",
                role="Admin",
                name="System Admin"
            )
            db.session.add(admin)
            db.session.commit()
            print(f"[✓] Created test admin with ID {admin.id}")

        # Clear existing entries
        AttendanceAdjustment.query.filter_by(employee_id=emp.id).delete()
        Attendance.query.filter_by(employee_id=emp.id).delete()
        db.session.commit()
        print("[✓] Cleared previous test records.")

        client = app.test_client()

        # Generate tokens
        token_payload = {"user_id": emp.id, "role": "Employee"}
        employee_token = jwt.encode(token_payload, app.config["JWT_SECRET_KEY"], algorithm=app.config["JWT_ALGORITHM"])
        employee_headers = {"Authorization": f"Bearer {employee_token}"}

        admin_payload = {"user_id": admin.id, "role": "Admin"}
        admin_token = jwt.encode(admin_payload, app.config["JWT_SECRET_KEY"], algorithm=app.config["JWT_ALGORITHM"])
        admin_headers = {"Authorization": f"Bearer {admin_token}"}

        # -------------------------------------------------------------
        # Test 1: Frontend Payload Generator Logic for Overnight Shifts
        # -------------------------------------------------------------
        print("\n--- Test 1: Payload Generation for Overnight Shift ---")
        selected_date = "2026-06-10"
        check_in_time = "18:00"
        check_out_time = "07:00"
        
        payload = build_payload(selected_date, check_in_time, check_out_time, "Overnight shift work regularization")
        
        print(f"Generated check_in:  {payload['check_in']}")
        print(f"Generated check_out: {payload['check_out']}")
        
        assert payload["check_in"] == "2026-06-10T18:00:00"
        assert payload["check_out"] == "2026-06-11T07:00:00"
        print("[PASS] - Overnight payload date incremented correctly.")

        # -------------------------------------------------------------
        # Test 2: Frontend Payload Generator Logic for Daytime Shifts
        # -------------------------------------------------------------
        print("\n--- Test 2: Payload Generation for Daytime Shift ---")
        payload_day = build_payload(selected_date, "09:00", "18:00", "Daytime work shift regularization")
        
        print(f"Generated check_in:  {payload_day['check_in']}")
        print(f"Generated check_out: {payload_day['check_out']}")
        
        assert payload_day["check_in"] == "2026-06-10T09:00:00"
        assert payload_day["check_out"] == "2026-06-10T18:00:00"
        print("[PASS] - Daytime payload dates remained on the same day.")

        # -------------------------------------------------------------
        # Test 3: Backend Submission Acceptance
        # -------------------------------------------------------------
        print("\n--- Test 3: Backend Submission of Overnight Payload ---")
        res = client.post("/api/attendance/regularization", json=payload, headers=employee_headers)
        print(f"Status: {res.status_code}")
        print(f"Response: {res.get_json()}")
        assert res.status_code == 201
        req_id = res.get_json()["request"]["id"]
        print("[PASS] - Backend successfully accepted the overnight request.")

        # -------------------------------------------------------------
        # Test 4: Approval Flow and working_hours calculation
        # -------------------------------------------------------------
        print("\n--- Test 4: Admin Approval & Hours Calculation ---")
        res_action = client.post(
            f"/api/attendance/regularization/{req_id}/action", 
            json={"status": "Approved", "comment": "Approved overnight shift"}, 
            headers=admin_headers
        )
        print(f"Status: {res_action.status_code}")
        assert res_action.status_code == 200
        
        # Verify Attendance database values
        att = Attendance.query.filter_by(employee_id=emp.id, date=datetime.strptime(selected_date, "%Y-%m-%d").date()).first()
        assert att is not None
        print(f"Recorded Check-in:  {att.check_in}")
        print(f"Recorded Check-out: {att.check_out}")
        print(f"Recorded Hours:     {att.working_hours}")
        
        assert float(att.working_hours) == 13.00
        print("[PASS] - Correct positive hours (13.00h) stored in database.")

        # Cleanup
        AttendanceAdjustment.query.filter_by(employee_id=emp.id).delete()
        Attendance.query.filter_by(employee_id=emp.id).delete()
        db.session.delete(emp)
        db.session.commit()
        print("\n[✓] All tests passed successfully!")

if __name__ == '__main__':
    run_tests()
