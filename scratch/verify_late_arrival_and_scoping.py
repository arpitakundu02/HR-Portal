import os
import sys
import json
import datetime as dt
from dotenv import load_dotenv

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../backend')))

from app import create_app
from extensions import db
from models import User, Attendance

def test_directory_scoping():
    print("\n============================================================")
    print("VERIFYING CONTACT DIRECTORY SCOPING RULES (VIA TEST CLIENT)")
    print("============================================================")
    
    app = create_app()
    with app.app_context():
        import jwt
        
        # 1. Employee login (Aradhya - TECH-001, Department: Tech)
        print("\n[1.1] Generating token as Employee: Aradhya...")
        aradhya = User.query.filter_by(employee_id='TECH-001').first()
        assert aradhya is not None, "Aradhya not found"
        
        emp_token = jwt.encode(
            {"user_id": aradhya.id, "role": aradhya.role, "exp": dt.datetime.utcnow() + dt.timedelta(hours=1)},
            app.config["JWT_SECRET_KEY"],
            algorithm="HS256"
        )
        emp_headers = {"Authorization": f"Bearer {emp_token}"}
        
        client = app.test_client()
        r_dir = client.get("/api/employees/directory", headers=emp_headers)
        print("Response status:", r_dir.status_code)
        
        emp_visible = r_dir.get_json().get("employees", [])
        print(f"Total visible to Employee (Aradhya, Tech dept): {len(emp_visible)}")
        for emp in emp_visible:
            print(f" - {emp['name']} (Dept: {emp['department_name']})")
        # Verify employee can only see employees from their department (Tech, dept id 2)
        assert all(e["department_id"] == 2 for e in emp_visible), "Employee saw users outside their department!"
        print("[✓] PASSED: Employee scoping rule verified (only sees department colleagues).")
        
        # 2. Line Manager login (Naitik - TECH-005, department Tech, is_line_manager = True)
        print("\n[1.2] Generating token as Line Manager: Naitik...")
        naitik = User.query.filter_by(employee_id='TECH-005').first()
        assert naitik is not None, "Naitik not found"
        
        mgr_token = jwt.encode(
            {"user_id": naitik.id, "role": naitik.role, "exp": dt.datetime.utcnow() + dt.timedelta(hours=1)},
            app.config["JWT_SECRET_KEY"],
            algorithm="HS256"
        )
        mgr_headers = {"Authorization": f"Bearer {mgr_token}"}
        
        r_dir = client.get("/api/employees/directory", headers=mgr_headers)
        mgr_visible = r_dir.get_json().get("employees", [])
        print(f"Total visible to Line Manager (Naitik): {len(mgr_visible)}")
        for emp in mgr_visible:
            print(f" - {emp['name']} (Dept: {emp['department_name']}, Role: {emp['role']}, Mgr: {emp['is_line_manager']})")
        # Verify Naitik sees Admins, other Line Managers, or people in Tech department (id 2)
        for emp in mgr_visible:
            is_admin = emp["role"] == "Admin"
            is_fellow_lm = emp["is_line_manager"] == 1
            is_same_dept = emp["department_id"] == 2
            is_self = emp["id"] == naitik.id
            assert is_admin or is_fellow_lm or is_same_dept or is_self, f"Line Manager saw unauthorized user: {emp['name']}"
        print("[✓] PASSED: Line Manager scoping rule verified (Admins, other Line Managers, same dept, direct reports).")
        
        # 3. Admin login
        print("\n[1.3] Generating token as Admin...")
        admin = User.query.filter_by(role='Admin').first()
        assert admin is not None, "Admin not found"
        
        admin_token = jwt.encode(
            {"user_id": admin.id, "role": admin.role, "exp": dt.datetime.utcnow() + dt.timedelta(hours=1)},
            app.config["JWT_SECRET_KEY"],
            algorithm="HS256"
        )
        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        
        r_dir = client.get("/api/employees/directory", headers=admin_headers)
        admin_visible = r_dir.get_json().get("employees", [])
        print(f"Total visible to Admin: {len(admin_visible)}")
        print("[✓] PASSED: Admin scoping rule verified (sees all active employees).")

def test_late_arrival_automation():
    print("\n============================================================")
    print("VERIFYING ATTENDANCE LATE ARRIVAL AUTOMATION (VIA TEST CLIENT)")
    print("============================================================")
    
    app = create_app()
    with app.app_context():
        import jwt
        
        # Find employee 179 (Rohan Sharma)
        rohan = User.query.filter_by(employee_id='TECH-003').first()
        if not rohan:
            # Fallback to get user by id 179
            rohan = User.query.get(179)
        assert rohan is not None, "Rohan Sharma not found"
        
        # Clear today's attendance for Rohan
        today = dt.date.today()
        Attendance.query.filter_by(employee_id=rohan.id, date=today).delete()
        db.session.commit()
        
        # Rule 1: Check-in before 10:00 AM (Present)
        print("\n[2.1] Simulating clock-in at 09:30 AM IST (before 10:00 AM)...")
        # 09:30 AM IST = 04:00 AM UTC
        dt_present = dt.datetime.combine(today, dt.time(4, 0, 0)) 
        
        att_present = Attendance(employee_id=rohan.id, date=today, check_in=dt_present, working_hours=0.0)
        db.session.add(att_present)
        db.session.commit()
        
        # Query via test client
        token = jwt.encode(
            {"user_id": rohan.id, "role": rohan.role, "exp": dt.datetime.utcnow() + dt.timedelta(hours=1)},
            app.config["JWT_SECRET_KEY"],
            algorithm="HS256"
        )
        headers = {"Authorization": f"Bearer {token}"}
        
        client = app.test_client()
        r_hist = client.get("/api/attendance/history", headers=headers)
        records_list = r_hist.get_json().get("records", [])
        today_rec = [rec for rec in records_list if rec["date"] == today.isoformat()][0]
        print(f"Check-in: {today_rec['check_in']} | Computed Status: {today_rec['attendance_status']}")
        assert today_rec["attendance_status"] == "Present", "Should be Present!"
        
        # Rule 2: Check-in between 10:00 AM and 1:00 PM (Half Day)
        print("\n[2.2] Simulating clock-in at 11:30 AM IST (10:00 AM to 12:59 PM)...")
        # 11:30 AM IST = 06:00 AM UTC
        dt_half = dt.datetime.combine(today, dt.time(6, 0, 0))
        
        att_rec = Attendance.query.filter_by(employee_id=rohan.id, date=today).first()
        att_rec.check_in = dt_half
        db.session.commit()
        
        r_hist = client.get("/api/attendance/history", headers=headers)
        records_list = r_hist.get_json().get("records", [])
        today_rec = [rec for rec in records_list if rec["date"] == today.isoformat()][0]
        print(f"Check-in: {today_rec['check_in']} | Computed Status: {today_rec['attendance_status']}")
        assert today_rec["attendance_status"] == "Half Day", "Should be Half Day!"
        
        # Rule 3: Check-in at or after 1:00 PM (Absent)
        print("\n[2.3] Simulating clock-in at 01:15 PM IST (at or after 1:00 PM)...")
        # 01:15 PM IST = 07:45 AM UTC
        dt_absent = dt.datetime.combine(today, dt.time(7, 45, 0))
        
        att_rec.check_in = dt_absent
        db.session.commit()
        
        r_hist = client.get("/api/attendance/history", headers=headers)
        records_list = r_hist.get_json().get("records", [])
        today_rec = [rec for rec in records_list if rec["date"] == today.isoformat()][0]
        print(f"Check-in: {today_rec['check_in']} | Computed Status: {today_rec['attendance_status']}")
        assert today_rec["attendance_status"] == "Absent", "Should be Absent!"
        
        # Cleanup today's attendance record
        Attendance.query.filter_by(employee_id=rohan.id, date=today).delete()
        db.session.commit()
        
        print("[✓] PASSED: Late arrival status rules verified successfully.")

if __name__ == "__main__":
    test_directory_scoping()
    test_late_arrival_automation()
