import os
import sys
import json
from datetime import datetime, timedelta, date

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))

from app import create_app
from extensions import db
from models import User, Task, Notification

def run_workflow():
    app = create_app()
    with app.app_context():
        # Setup test data
        employee = User(
            employee_id="TEST-TSK-01",
            email="test_tsk@company.com",
            name="Task Tester",
            role="Employee",
            password_hash="hashed"
        )
        admin = User(
            employee_id="TEST-TSK-ADM",
            email="test_tsk_adm@company.com",
            name="Task Admin",
            role="Admin",
            password_hash="hashed"
        )
        db.session.add_all([employee, admin])
        db.session.commit()

        # Generate JWT client tokens
        import jwt
        token = jwt.encode(
            {"user_id": employee.id, "role": "Employee", "exp": datetime.utcnow() + timedelta(hours=1)},
            app.config["JWT_SECRET_KEY"],
            algorithm="HS256"
        )
        admin_token = jwt.encode(
            {"user_id": admin.id, "role": "Admin", "exp": datetime.utcnow() + timedelta(hours=1)},
            app.config["JWT_SECRET_KEY"],
            algorithm="HS256"
        )

        client = app.test_client()

        # 1. Admin assigns task to employee
        res = client.post("/api/tasks/",
                          headers={"Authorization": f"Bearer {admin_token}"},
                          data=json.dumps({
                              "title": "Task Assigned by Admin",
                              "description": "Complete assignment",
                              "employee_id": employee.id,
                              "due_date": (date.today() + timedelta(days=2)).isoformat()
                          }),
                          content_type="application/json")
        assert res.status_code == 201, f"Task creation failed: {res.data}"
        task_data = json.loads(res.data)

        # Verify DB entry
        task = Task.query.get(task_data["id"])
        assert task.status == "Pending", "Task status not pending"

        # Verify email/notification generated (Mock)
        notif = Notification.query.filter_by(user_id=employee.id).first()
        assert notif is not None, "Task assignee notification not generated"

        # 2. Employee updates task status
        res_update = client.put(f"/api/tasks/{task.id}",
                                headers={"Authorization": f"Bearer {token}"},
                                data=json.dumps({
                                    "status": "In Progress"
                                }),
                                content_type="application/json")
        assert res_update.status_code == 200, f"Task update failed: {res_update.data}"

        # Verify status synchronization
        db.session.refresh(task)
        assert task.status == "In Progress", "Task status not In Progress in DB"

        # Cleanup
        db.session.delete(task)
        Notification.query.filter(Notification.user_id.in_([employee.id, admin.id])).delete()
        db.session.delete(employee)
        db.session.delete(admin)
        db.session.commit()

        print("PASS: Tasks Workflow")

if __name__ == "__main__":
    run_workflow()
