import os
import sys
import json
from datetime import datetime, timedelta

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))

from app import create_app
from extensions import db
from models import User, UserProfileUpdate, ApprovalRequest, Notification

def run_workflow():
    app = create_app()
    with app.app_context():
        # Setup test data
        employee = User(
            employee_id="TEST-PROF-01",
            email="test_prof@company.com",
            name="Profile Tester",
            role="Employee",
            password_hash="hashed",
            fathers_name="Old Father"
        )
        manager = User(
            employee_id="TEST-PROF-MGR",
            email="test_prof_mgr@company.com",
            name="Profile Manager",
            role="Employee",
            password_hash="hashed"
        )
        db.session.add_all([employee, manager])
        db.session.commit()

        employee.manager_id = manager.id
        db.session.commit()

        # Generate JWT client tokens
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

        # 1. Create Profile Update Request
        res = client.post("/api/profile/update-request",
                          headers={"Authorization": f"Bearer {token}"},
                          data=json.dumps({
                              "requested_changes": {
                                  "fathers_name": "New Father",
                                  "blood_group": "O+"
                              }
                          }),
                          content_type="application/json")
        assert res.status_code == 201, f"Profile request failed: {res.data}"
        prof_data = json.loads(res.data)

        # Verify DB entry
        profile_req = UserProfileUpdate.query.get(prof_data["request"]["id"])
        assert profile_req.status == "Pending", "Profile status not pending"

        # Verify Approval routing
        app_req = ApprovalRequest.query.get(profile_req.approval_request_id)
        assert app_req is not None, "Approval request not generated"
        assert app_req.approver_id == manager.id, "Approver not routed to manager"

        # 2. Prevent Duplicate profile update requests
        res_dup = client.post("/api/profile/update-request",
                              headers={"Authorization": f"Bearer {token}"},
                              data=json.dumps({
                                  "requested_changes": {
                                      "fathers_name": "Another Father"
                                  }
                              }),
                              content_type="application/json")
        assert res_dup.status_code == 409, f"Allowed duplicate pending request: {res_dup.data}"

        # 3. Action Profile Request (Approve)
        res_act = client.post(f"/api/approvals/{app_req.id}/action",
                              headers={"Authorization": f"Bearer {mgr_token}"},
                              data=json.dumps({"status": "Approved", "comments": "Verified info"}),
                              content_type="application/json")
        assert res_act.status_code == 200, f"Approve failed: {res_act.data}"

        # Verify profile changes applied to User record & synchronization
        db.session.refresh(employee)
        db.session.refresh(profile_req)
        db.session.refresh(app_req)
        assert employee.fathers_name == "New Father", "Profile fathers name not updated on User record"
        assert employee.blood_group == "O+", "Profile blood group not updated on User record"
        assert profile_req.status == "Approved", "Profile request status not synchronized to Approved"
        assert app_req.status == "Approved", "ApprovalRequest status not Approved"

        # Cleanup
        db.session.delete(profile_req)
        db.session.delete(app_req)
        Notification.query.filter(Notification.user_id.in_([employee.id, manager.id])).delete()
        db.session.delete(employee)
        db.session.delete(manager)
        db.session.commit()

        print("PASS: Profile Update Requests Workflow")

if __name__ == "__main__":
    run_workflow()
