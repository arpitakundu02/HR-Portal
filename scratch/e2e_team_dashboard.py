# scratch/e2e_team_dashboard.py
import os
import sys
import json
from datetime import datetime, timedelta, date
import datetime as dt

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))

from app import create_app
from extensions import db
from models import User, Attendance, Task, Timesheet, Meeting, ApprovalRequest

def _get_company_date() -> date:
    kolkata_tz = dt.timezone(dt.timedelta(hours=5, minutes=30))
    return dt.datetime.now(kolkata_tz).date()

def run_workflow():
    app = create_app()
    with app.app_context():
        # Setup test data
        admin = User(
            employee_id="TEST-TDB-ADM",
            email="tdb_admin@company.com",
            name="TDB Admin",
            role="Admin",
            password_hash="hashed"
        )
        supervisor = User(
            employee_id="TEST-TDB-SUP",
            email="tdb_super@company.com",
            name="TDB Supervisor",
            role="Employee",
            password_hash="hashed"
        )
        
        try:
            db.session.add_all([admin, supervisor])
            db.session.commit()

            # Employee reporting to Supervisor
            employee = User(
                employee_id="TEST-TDB-EMP",
                email="tdb_emp@company.com",
                name="TDB Employee",
                role="Employee",
                manager_id=supervisor.id,
                password_hash="hashed"
            )
            # Unrelated employee reporting to no one
            other_employee = User(
                employee_id="TEST-TDB-OTH",
                email="tdb_oth@company.com",
                name="Other TDB Employee",
                role="Employee",
                password_hash="hashed"
            )
            db.session.add_all([employee, other_employee])
            db.session.commit()

            today = _get_company_date()

            # 1. Today's attendance for the direct report
            attendance = Attendance(
                employee_id=employee.id,
                date=today,
                check_in=datetime.combine(today, dt.time(3, 0, 0)),
                working_hours=0.0
            )
            # 2. Today's task for the direct report
            task = Task(
                title="Dashboard Task",
                employee_id=employee.id,
                status="Pending",
                assigned_by=supervisor.id
            )
            # 3. Daily timesheet log for the direct report
            timesheet = Timesheet(
                employee_id=employee.id,
                date=today,
                task_name="Dashboard integration E2E",
                hours_spent=4.0,
                description="Testing dashboard E2E metrics",
                status="Submitted"
            )

            db.session.add_all([attendance, task, timesheet])
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

            client = app.test_client()

            # 1. Fetch metadata for supervisor
            res = client.get("/api/team-dashboard/metadata", headers={"Authorization": f"Bearer {token_sup}"})
            assert res.status_code == 200, f"Metadata call failed: {res.data}"
            meta_data = json.loads(res.data)
            assert meta_data["is_supervisor"] is True
            assert meta_data["reports_count"] == 1

            # 2. Fetch metadata for non-supervisor employee
            res = client.get("/api/team-dashboard/metadata", headers={"Authorization": f"Bearer {token_oth}"})
            assert res.status_code == 200
            meta_data_oth = json.loads(res.data)
            assert meta_data_oth["is_supervisor"] is False
            assert meta_data_oth["reports_count"] == 0

            # 3. Fetch team stats as supervisor
            res = client.get("/api/team-dashboard/stats", headers={"Authorization": f"Bearer {token_sup}"})
            assert res.status_code == 200, f"Stats call failed: {res.data}"
            stats = json.loads(res.data)
            assert stats["present_today"] == 1
            assert stats["pending_tasks"] == 1
            assert len(stats["recent_timesheets"]) == 1
            assert stats["recent_timesheets"][0]["task_name"] == "Dashboard integration E2E"

            print("PASS: Team Dashboard Workflow E2E Verification")

        finally:
            # Cleanup
            try:
                Timesheet.query.filter(Timesheet.employee_id == employee.id).delete()
            except Exception:
                pass
            try:
                Task.query.filter(Task.employee_id == employee.id).delete()
            except Exception:
                pass
            try:
                Attendance.query.filter(Attendance.employee_id == employee.id).delete()
            except Exception:
                pass
            try:
                db.session.delete(employee)
            except Exception:
                pass
            try:
                db.session.delete(other_employee)
            except Exception:
                pass
            try:
                db.session.delete(supervisor)
            except Exception:
                pass
            try:
                db.session.delete(admin)
            except Exception:
                pass
            db.session.commit()

if __name__ == "__main__":
    run_workflow()
