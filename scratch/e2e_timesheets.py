# scratch/e2e_timesheets.py
import os
import sys
import json
from datetime import datetime, timedelta, date

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))

from app import create_app
from extensions import db
from models import User, Timesheet

def run_workflow():
    app = create_app()
    with app.app_context():
        # Setup test data
        admin = User(
            employee_id="TEST-TS-ADM",
            email="ts_admin@company.com",
            name="Timesheet Admin",
            role="Admin",
            password_hash="hashed"
        )
        supervisor = User(
            employee_id="TEST-TS-SUP",
            email="ts_super@company.com",
            name="Timesheet Supervisor",
            role="Employee",
            password_hash="hashed"
        )
        db.session.add_all([admin, supervisor])
        db.session.commit()

        # Employee reporting to Supervisor
        employee = User(
            employee_id="TEST-TS-EMP",
            email="ts_emp@company.com",
            name="Timesheet Employee",
            role="Employee",
            manager_id=supervisor.id,
            password_hash="hashed"
        )
        # Unrelated employee reporting to no one
        other_employee = User(
            employee_id="TEST-TS-OTH",
            email="ts_oth@company.com",
            name="Other Employee",
            role="Employee",
            password_hash="hashed"
        )
        db.session.add_all([employee, other_employee])
        db.session.commit()

        # Generate JWT client tokens
        import jwt
        token_emp = jwt.encode(
            {"user_id": employee.id, "role": "Employee", "exp": datetime.utcnow() + timedelta(hours=1)},
            app.config["JWT_SECRET_KEY"],
            algorithm="HS256"
        )
        token_sup = jwt.encode(
            {"user_id": supervisor.id, "role": "Employee", "exp": datetime.utcnow() + timedelta(hours=1)},
            app.config["JWT_SECRET_KEY"],
            algorithm="HS256"
        )
        token_oth = jwt.encode(
            {"user_id": other_employee.id, "role": "Employee", "exp": datetime.utcnow() + timedelta(hours=1)},
            app.config["JWT_SECRET_KEY"],
            algorithm="HS256"
        )
        token_adm = jwt.encode(
            {"user_id": admin.id, "role": "Admin", "exp": datetime.utcnow() + timedelta(hours=1)},
            app.config["JWT_SECRET_KEY"],
            algorithm="HS256"
        )

        client = app.test_client()

        # 1. Employee submits a timesheet
        res = client.post("/api/timesheets",
                          headers={"Authorization": f"Bearer {token_emp}"},
                          data=json.dumps({
                              "date": "2026-06-10",
                              "task_name": "Implement Timesheet module",
                              "hours_spent": 8.0,
                              "description": "Implemented backend and frontend timesheet requirements"
                          }),
                          content_type="application/json")
        assert res.status_code == 201, f"Timesheet submission failed: {res.data}"
        ts_data = json.loads(res.data)["timesheet"]

        # Verify DB entry
        ts_id = ts_data["id"]
        ts_db = Timesheet.query.get(ts_id)
        assert ts_db is not None
        assert ts_db.task_name == "Implement Timesheet module"
        assert ts_db.status == "Submitted"

        # 2. Employee views their own timesheet history
        res = client.get("/api/timesheets", headers={"Authorization": f"Bearer {token_emp}"})
        assert res.status_code == 200
        history = json.loads(res.data)
        assert len(history) >= 1
        assert history[0]["id"] == ts_id

        # 3. Supervisor fetches timesheets of their team (direct reports)
        res = client.get("/api/timesheets/team", headers={"Authorization": f"Bearer {token_sup}"})
        assert res.status_code == 200
        team_logs = json.loads(res.data)
        assert len(team_logs) == 1
        assert team_logs[0]["id"] == ts_id

        # 4. Supervisor filters by employee and date
        res = client.get(f"/api/timesheets/team?employee_id={employee.id}&date=2026-06-10",
                         headers={"Authorization": f"Bearer {token_sup}"})
        assert res.status_code == 200
        filtered_logs = json.loads(res.data)
        assert len(filtered_logs) == 1

        # 5. Non-supervisor employee views team timesheets (should return empty list)
        res = client.get("/api/timesheets/team", headers={"Authorization": f"Bearer {token_oth}"})
        assert res.status_code == 200
        oth_team_logs = json.loads(res.data)
        assert len(oth_team_logs) == 0

        # 6. Admin can view all timesheets
        res = client.get("/api/timesheets/team", headers={"Authorization": f"Bearer {token_adm}"})
        assert res.status_code == 200
        admin_logs = json.loads(res.data)
        assert len(admin_logs) >= 1

        # Cleanup
        Timesheet.query.filter_by(employee_id=employee.id).delete()
        db.session.delete(employee)
        db.session.delete(other_employee)
        db.session.delete(supervisor)
        db.session.delete(admin)
        db.session.commit()

        print("PASS: Timesheet Workflow E2E Verification")

if __name__ == "__main__":
    run_workflow()
