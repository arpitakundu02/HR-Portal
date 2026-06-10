import os
import sys
import json
from datetime import datetime, timedelta, date

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))

from app import create_app
from extensions import db
from models import User, Meeting, Notification

def run_workflow():
    app = create_app()
    with app.app_context():
        # Setup test data
        employee = User(
            employee_id="TEST-MTG-01",
            email="test_mtg@company.com",
            name="Meeting Tester",
            role="Employee",
            password_hash="hashed"
        )
        admin = User(
            employee_id="TEST-MTG-ADM",
            email="test_mtg_adm@company.com",
            name="Meeting Admin",
            role="Admin",
            password_hash="hashed"
        )
        db.session.add_all([employee, admin])
        db.session.commit()

        # Create department
        from models import Department
        dept = Department(name="Meeting Department", manager_id=admin.id)
        db.session.add(dept)
        db.session.commit()

        employee.department_id = dept.id
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

        # 1. Admin schedules a meeting
        scheduled_time = (datetime.utcnow() + timedelta(days=1)).isoformat() + "Z"
        res = client.post("/api/meetings/",
                          headers={"Authorization": f"Bearer {admin_token}"},
                          data=json.dumps({
                              "title": "Strategy Catchup",
                              "description": "Discuss future plans",
                              "department_id": dept.id,
                              "scheduled_at": scheduled_time,
                              "duration_minutes": 60,
                              "link": "https://zoom.us/j/123456"
                          }),
                          content_type="application/json")
        assert res.status_code == 201, f"Meeting scheduling failed: {res.data}"
        mtg_data = json.loads(res.data)

        # Verify DB entry
        meeting = Meeting.query.get(mtg_data["id"])
        assert meeting.title == "Strategy Catchup", "Meeting title not matched in DB"

        # Verify employee gets listed meetings
        res_list = client.get("/api/meetings/", headers={"Authorization": f"Bearer {token}"})
        assert res_list.status_code == 200
        list_data = json.loads(res_list.data)
        meeting_ids = [m["id"] for m in list_data]
        assert meeting.id in meeting_ids, "Employee cannot see scheduled department meeting"

        # Cleanup
        db.session.delete(meeting)
        db.session.delete(dept)
        Notification.query.filter(Notification.user_id.in_([employee.id, admin.id])).delete()
        db.session.delete(employee)
        db.session.delete(admin)
        db.session.commit()

        print("PASS: Meetings Workflow")

if __name__ == "__main__":
    run_workflow()
