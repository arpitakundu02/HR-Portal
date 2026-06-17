# scratch/e2e_line_manager.py
import os
import sys
import json
from datetime import datetime, timedelta

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))

from app import create_app
from extensions import db
from models import User

def run_workflow():
    app = create_app()
    with app.app_context():
        print("[*] Setting up Line Manager E2E verification test data...")
        
        # 1. Create Admin
        admin = User(
            employee_id="LM-ADM-TEST",
            email="lm_admin@company.com",
            name="LM Admin",
            role="Admin",
            password_hash="hashed"
        )
        # 2. Create Employee to be designated as Line Manager
        lm = User(
            employee_id="LM-SUP-TEST",
            email="lm_sup@company.com",
            name="LM Supervisor",
            role="Employee",
            password_hash="hashed",
            is_line_manager=False
        )
        
        try:
            db.session.add(admin)
            db.session.add(lm)
            db.session.commit()

            # Generate JWT tokens
            import jwt
            token_admin = jwt.encode(
                {"user_id": admin.id, "role": "Admin", "exp": datetime.utcnow() + timedelta(hours=1)},
                app.config["JWT_SECRET_KEY"],
                algorithm="HS256"
            )
            token_lm = jwt.encode(
                {"user_id": lm.id, "role": "Employee", "exp": datetime.utcnow() + timedelta(hours=1)},
                app.config["JWT_SECRET_KEY"],
                algorithm="HS256"
            )

            client = app.test_client()

            # Verification 1: Standard employee cannot create employees
            res = client.post("/api/employees/", json={
                "name": "Should Fail",
                "email": "fail@company.com",
                "password": "password123"
            }, headers={"Authorization": f"Bearer {token_lm}"})
            assert res.status_code == 403, f"Standard employee should not create employees: {res.data}"

            # Verification 2: Admin designates Employee as a Line Manager
            res = client.put(f"/api/employees/{lm.id}", json={
                "is_line_manager": True
            }, headers={"Authorization": f"Bearer {token_admin}"})
            assert res.status_code == 200, f"Failed to designate line manager: {res.data}"
            
            # Refresh LM object from database
            db.session.refresh(lm)
            assert lm.is_line_manager is True, "is_line_manager flag was not set to True"

            # Generate fresh JWT token for Line Manager (just in case)
            token_lm = jwt.encode(
                {"user_id": lm.id, "role": "Employee", "exp": datetime.utcnow() + timedelta(hours=1)},
                app.config["JWT_SECRET_KEY"],
                algorithm="HS256"
            )

            # Verification 3: Designated Line Manager creates an Employee
            res = client.post("/api/employees/", json={
                "name": "Direct Report",
                "email": "report@company.com",
                "password": "password123",
                "rank": "Developer"
            }, headers={"Authorization": f"Bearer {token_lm}"})
            assert res.status_code == 201, f"Line manager failed to create employee: {res.data}"
            
            report_data = json.loads(res.data)
            report_id = report_data["id"]

            # Verification 4: Created employee has manager_id set to Line Manager's ID automatically
            db_report = User.query.get(report_id)
            assert db_report.manager_id == lm.id, f"Auto manager assignment failed: manager_id is {db_report.manager_id}, expected {lm.id}"

            # Verification 5: Line Manager can view their direct reports (scoped)
            res = client.get("/api/employees/", headers={"Authorization": f"Bearer {token_lm}"})
            assert res.status_code == 200
            employees_list = json.loads(res.data)["employees"]
            visible_ids = [emp["id"] for emp in employees_list]
            assert report_id in visible_ids, f"Expected direct report ID {report_id} to be visible, got {visible_ids}"
            for emp in employees_list:
                is_admin = emp["role"] == "Admin"
                is_fellow_lm = emp["is_line_manager"] == 1 or emp["is_line_manager"] is True
                is_direct_report = emp["id"] == report_id
                assert is_admin or is_fellow_lm or is_direct_report, f"Unauthorized employee in list: {emp['name']}"

            # Verification 6: Line Manager can manage / edit direct reports
            res = client.put(f"/api/employees/{report_id}", json={
                "rank": "Senior Developer",
                "salary": 60000
            }, headers={"Authorization": f"Bearer {token_lm}"})
            assert res.status_code == 200, f"Line manager failed to edit report: {res.data}"
            
            db.session.refresh(db_report)
            assert db_report.rank == "Senior Developer", "Rank update failed"
            assert float(db_report.salary) == 60000, "Salary update failed"

            # Verification 7: A different employee outside hierarchy cannot access or modify the direct report
            other_emp = User(
                employee_id="LM-OTH-TEST",
                email="lm_oth@company.com",
                name="LM Other",
                role="Employee",
                password_hash="hashed"
            )
            db.session.add(other_emp)
            db.session.commit()

            token_oth = jwt.encode(
                {"user_id": other_emp.id, "role": "Employee", "exp": datetime.utcnow() + timedelta(hours=1)},
                app.config["JWT_SECRET_KEY"],
                algorithm="HS256"
            )

            res = client.get(f"/api/employees/{report_id}", headers={"Authorization": f"Bearer {token_oth}"})
            assert res.status_code == 403, f"Unauthorized employee should not view report: {res.data}"

            res = client.put(f"/api/employees/{report_id}", json={"rank": "Hacker"}, headers={"Authorization": f"Bearer {token_oth}"})
            assert res.status_code == 403, f"Unauthorized employee should not edit report: {res.data}"

        finally:
            # Cleanup
            try:
                db.session.query(User).filter(User.employee_id == "Direct Report").delete()
            except Exception:
                pass
            try:
                db_report_id = User.query.filter_by(email="report@company.com").first()
                if db_report_id:
                    db.session.delete(db_report_id)
            except Exception:
                pass
            try:
                db.session.delete(other_emp)
            except Exception:
                pass
            try:
                db.session.delete(lm)
            except Exception:
                pass
            try:
                db.session.delete(admin)
            except Exception:
                pass
            db.session.commit()

        print("PASS: Line Manager Workflow E2E Verification")

if __name__ == "__main__":
    run_workflow()
