import os
import sys
import json
from datetime import datetime, timedelta, date

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))

from app import create_app
from extensions import db
from models import User, Attendance, AttendanceAdjustment, ApprovalRequest, Notification
from utils.approval_callbacks import ApprovalCallbackRegistry

def run_workflow():
    app = create_app()
    with app.app_context():
        # Setup test data
        employee = User(
            employee_id="TEST-ATT-01",
            email="test_att@company.com",
            name="Attendance Tester",
            role="Employee",
            password_hash="hashed"
        )
        manager = User(
            employee_id="TEST-ATT-MGR",
            email="test_att_mgr@company.com",
            name="Attendance Manager",
            role="Employee",
            password_hash="hashed"
        )
        db.session.add_all([employee, manager])
        db.session.commit()
        
        employee.manager_id = manager.id
        db.session.commit()

        # Update office coordinates setting to match the test check-in coordinates
        from models import SystemSetting
        lat_setting = SystemSetting.query.filter_by(key="office_latitude").first()
        lon_setting = SystemSetting.query.filter_by(key="office_longitude").first()
        rad_setting = SystemSetting.query.filter_by(key="office_radius").first()
        
        # Backup original office settings if they exist to restore later
        orig_lat = lat_setting.value if lat_setting else None
        orig_lon = lon_setting.value if lon_setting else None
        
        if lat_setting:
            lat_setting.value = "28.6139"
        else:
            db.session.add(SystemSetting(key="office_latitude", value="28.6139"))
            
        if lon_setting:
            lon_setting.value = "77.2090"
        else:
            db.session.add(SystemSetting(key="office_longitude", value="77.2090"))
            
        if not rad_setting:
            db.session.add(SystemSetting(key="office_radius", value="500"))
            
        db.session.commit()

        # Generate JWT client test token
        import jwt
        token = jwt.encode(
            {"user_id": employee.id, "role": "Employee", "exp": datetime.utcnow() + timedelta(hours=1)},
            app.config["JWT_SECRET_KEY"],
            algorithm="HS256"
        )
        mgr_token = jwt.encode(
            {"user_id": manager.id, "role": "Employee", "exp": datetime.utcnow() + timedelta(hours=1)},
            app.config["JWT_SECRET_KEY"],
            algorithm="HS256"
        )

        client = app.test_client()

        # 1. Check In via API
        res = client.post("/api/attendance/checkin",
                          headers={"Authorization": f"Bearer {token}"},
                          data=json.dumps({"latitude": 28.6139, "longitude": 77.2090}),
                          content_type="application/json")
        assert res.status_code == 201, f"Checkin failed: {res.data}"

        # Verify DB state
        record = Attendance.query.filter_by(employee_id=employee.id, date=date.today()).first()
        assert record is not None, "Attendance record not found in DB"
        assert record.check_in is not None, "Check-in timestamp not set"

        # 2. Check Out via API
        res = client.post("/api/attendance/checkout",
                          headers={"Authorization": f"Bearer {token}"})
        assert res.status_code == 200, f"Checkout failed: {res.data}"
        db.session.refresh(record)
        assert record.check_out is not None, "Check-out timestamp not set in DB"

        # 3. Create Attendance Regularization Request
        past_date = (date.today() - timedelta(days=2))
        res = client.post("/api/attendance/regularization",
                          headers={"Authorization": f"Bearer {token}"},
                          data=json.dumps({
                              "date": past_date.isoformat(),
                              "check_in": (datetime.combine(past_date, datetime.min.time()) + timedelta(hours=9)).isoformat() + "Z",
                              "check_out": (datetime.combine(past_date, datetime.min.time()) + timedelta(hours=17)).isoformat() + "Z",
                              "reason": "Forgot to check-in"
                          }),
                          content_type="application/json")
        assert res.status_code == 201, f"Regularization request failed: {res.data}"
        adj_data = json.loads(res.data)

        # Verify DB state updates
        adj = AttendanceAdjustment.query.get(adj_data["request"]["id"])
        assert adj.status == "Pending", "Adjustment status not pending"

        # 4. Action Regularization (Approve) via API (requires Admin)
        # Generate Admin token for actioning
        admin = User(
            employee_id="TEST-ATT-ADM",
            email="test_att_adm@company.com",
            name="Attendance Admin",
            role="Admin",
            password_hash="hashed"
        )
        db.session.add(admin)
        db.session.commit()
        admin_token = jwt.encode(
            {"user_id": admin.id, "role": "Admin", "exp": datetime.utcnow() + timedelta(hours=1)},
            app.config["JWT_SECRET_KEY"],
            algorithm="HS256"
        )

        res = client.post(f"/api/attendance/regularization/{adj.id}/action",
                          headers={"Authorization": f"Bearer {admin_token}"},
                          data=json.dumps({"status": "Approved", "comment": "Okay"}),
                          content_type="application/json")
        assert res.status_code == 200, f"Action regularization failed: {res.data}"

        # Verify DB update applied
        db.session.refresh(adj)
        assert adj.status == "Approved", "Adjustment not approved in DB"
        
        reg_record = Attendance.query.filter_by(employee_id=employee.id, date=past_date).first()
        assert reg_record is not None, "Regularized attendance record not created"
        assert reg_record.working_hours > 0, "Working hours not calculated"

        # Cleanup
        db.session.delete(reg_record)
        db.session.delete(record)
        db.session.delete(adj)
        # Restore office settings
        if orig_lat is not None:
            lat_setting.value = orig_lat
        else:
            db.session.delete(lat_setting)
        if orig_lon is not None:
            lon_setting.value = orig_lon
        else:
            db.session.delete(lon_setting)
        # Delete related notifications
        Notification.query.filter((Notification.user_id == employee.id) | (Notification.user_id == manager.id)).delete()
        db.session.delete(employee)
        db.session.delete(manager)
        db.session.delete(admin)
        db.session.commit()

        print("PASS: Attendance & Regularization Workflow")

if __name__ == "__main__":
    run_workflow()
