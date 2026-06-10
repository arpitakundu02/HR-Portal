import os
import sys
import json
from datetime import datetime, timedelta, date

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))

from app import create_app
from extensions import db
from models import User, Announcement, Notification

def run_workflow():
    app = create_app()
    with app.app_context():
        # Setup test data
        employee = User(
            employee_id="TEST-ANN-01",
            email="test_ann@company.com",
            name="Announcement Tester",
            role="Employee",
            password_hash="hashed"
        )
        admin = User(
            employee_id="TEST-ANN-ADM",
            email="test_ann_adm@company.com",
            name="Announcement Admin",
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

        # 1. Admin creates Announcement
        res = client.post("/api/announcements/",
                          headers={"Authorization": f"Bearer {admin_token}"},
                          data=json.dumps({
                              "title": "Townhall Update",
                              "content": "A townhall is scheduled for Friday",
                              "audience_type": "All",
                              "is_active": True
                          }),
                          content_type="application/json")
        assert res.status_code == 201, f"Announcement creation failed: {res.data}"
        ann_data = json.loads(res.data)

        # Verify DB entry
        ann = Announcement.query.get(ann_data["id"])
        assert ann.title == "Townhall Update", "Announcement title not matching in DB"

        # Verify automated notification generated for employee
        notif = Notification.query.filter_by(user_id=employee.id, notification_type="Announcement").first()
        assert notif is not None, "Automated announcement notification not generated"

        # 2. Employee views announcements
        res_list = client.get("/api/announcements/active", headers={"Authorization": f"Bearer {token}"})
        assert res_list.status_code == 200
        list_data = json.loads(res_list.data)
        ann_ids = [a["id"] for a in list_data]
        assert ann.id in ann_ids, "Active announcement not visible to employee"

        # Cleanup
        db.session.delete(ann)
        Notification.query.filter(Notification.user_id.in_([employee.id, admin.id])).delete()
        db.session.delete(employee)
        db.session.delete(admin)
        db.session.commit()

        print("PASS: Announcements & Notifications Workflow")

if __name__ == "__main__":
    run_workflow()
