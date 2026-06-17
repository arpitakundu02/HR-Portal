import os
import sys
import json
from datetime import datetime, timedelta, date

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))

from app import create_app
from extensions import db
from models import User, RegistrationRequest, LeaveBalance

def run_workflow():
    app = create_app()
    with app.app_context():
        # Cleanup pre-existing users or registration requests
        existing_admin = User.query.filter_by(employee_id="TEST-REG-ADM").first()
        if existing_admin:
            db.session.delete(existing_admin)
        
        candidates = User.query.filter(User.email.in_(["test_candidate@company.com", "reject_candidate@company.com"])).all()
        for c in candidates:
            LeaveBalance.query.filter_by(employee_id=c.id).delete()
            db.session.delete(c)

        RegistrationRequest.query.filter(RegistrationRequest.email.in_(["test_candidate@company.com", "reject_candidate@company.com"])).delete()
        db.session.commit()

        # Setup Admin for approving/rejecting requests
        admin = User(
            employee_id="TEST-REG-ADM",
            email="test_reg_adm@company.com",
            name="Registration Admin",
            role="Admin",
            password_hash="hashed"
        )
        db.session.add(admin)
        db.session.commit()

        # Generate JWT client token for Admin
        import jwt
        admin_token = jwt.encode(
            {"user_id": admin.id, "role": "Admin", "exp": datetime.utcnow() + timedelta(hours=1)},
            app.config["JWT_SECRET_KEY"],
            algorithm="HS256"
        )

        client = app.test_client()

        # 1. Public user submits registration request
        reg_payload = {
            "email": "test_candidate@company.com",
            "password": "candidatepassword123",
            "name": "Candidate Tester",
            "fathers_name": "Father Tester",
            "dob": "1995-05-15",
            "blood_group": "B+",
            "address": "123 Test St, India"
        }
        res = client.post("/api/registrations/register",
                           data=json.dumps(reg_payload),
                           content_type="application/json")
        assert res.status_code == 201, f"Registration submission failed: {res.data}"
        res_data = json.loads(res.data)
        assert res_data["request"]["email"] == "test_candidate@company.com"
        assert res_data["request"]["status"] == "Pending"

        req_id = res_data["request"]["id"]

        # 2. Duplicate registration attempt check (should fail with 409)
        res_dup = client.post("/api/registrations/register",
                              data=json.dumps(reg_payload),
                              content_type="application/json")
        assert res_dup.status_code == 409, f"Duplicate registration did not return 409: {res_dup.status_code}"

        # 3. Test Rejection Workflow
        # Let's create a temporary registration request to reject
        reject_payload = {
            "email": "reject_candidate@company.com",
            "password": "rejectpassword123",
            "name": "Rejected Tester"
        }
        res_rej_req = client.post("/api/registrations/register",
                                  data=json.dumps(reject_payload),
                                  content_type="application/json")
        assert res_rej_req.status_code == 201
        rej_req_id = json.loads(res_rej_req.data)["request"]["id"]

        # Action rejection (requires Admin auth)
        res_rej_action = client.post(f"/api/registrations/requests/{rej_req_id}/action",
                                     headers={"Authorization": f"Bearer {admin_token}"},
                                     data=json.dumps({
                                         "status": "Rejected",
                                         "rejection_reason": "Incomplete profile documentation."
                                     }),
                                     content_type="application/json")
        assert res_rej_action.status_code == 200
        rej_data = json.loads(res_rej_action.data)["request"]
        assert rej_data["status"] == "Rejected"
        assert rej_data["rejection_reason"] == "Incomplete profile documentation."

        # Verify that Rejected user account is NOT created in User model
        rej_user = User.query.filter_by(email="reject_candidate@company.com").first()
        assert rej_user is None, "Rejected candidate was incorrectly created as User"

        # 4. Test Approval Workflow
        # Approve the first candidate (Candidate Tester)
        res_app_action = client.post(f"/api/registrations/requests/{req_id}/action",
                                     headers={"Authorization": f"Bearer {admin_token}"},
                                     data=json.dumps({
                                         "status": "Approved"
                                     }),
                                     content_type="application/json")
        assert res_app_action.status_code == 200
        app_data = json.loads(res_app_action.data)["request"]
        assert app_data["status"] == "Approved"

        # 5. Verify Employee Account Generation on Approval
        emp_user = User.query.filter_by(email="test_candidate@company.com").first()
        assert emp_user is not None, "Approved candidate user account not found in DB"
        assert emp_user.name == "Candidate Tester"
        assert emp_user.role == "Employee"
        assert emp_user.is_active is True
        assert emp_user.fathers_name == "Father Tester"
        assert emp_user.dob == date(1995, 5, 15)
        assert emp_user.blood_group == "B+"
        assert emp_user.address == "123 Test St, India"
        assert emp_user.employee_id.startswith("HR-"), f"Employee ID {emp_user.employee_id} does not follow auto-generation logic"

        # Verify leave balances initialized to correct default rules (APL=20, WFH=4 for Male)
        balances = LeaveBalance.query.filter_by(employee_id=emp_user.id).all()
        assert len(balances) == 2, f"Leave balances not initialized correctly: {balances}"
        for bal in balances:
            assert bal.leave_type in ["APL", "WFH"]
            expected_allocated = 20 if bal.leave_type == "APL" else 4
            assert bal.allocated == expected_allocated, f"Expected {expected_allocated} for {bal.leave_type}, got {bal.allocated}"
            assert bal.used == 0
            assert bal.remaining == expected_allocated, f"Expected remaining {expected_allocated} for {bal.leave_type}, got {bal.remaining}"

        # 6. Test Login after approval using auth endpoint
        login_res = client.post("/api/auth/login",
                                data=json.dumps({
                                    "email": "test_candidate@company.com",
                                    "password": "candidatepassword123",
                                    "role": "Employee"
                                }),
                                content_type="application/json")
        assert login_res.status_code == 200, f"Login failed for newly approved user: {login_res.data}"
        login_data = json.loads(login_res.data)
        assert "token" in login_data
        assert login_data["user"]["name"] == "Candidate Tester"

        # Cleanup
        db.session.delete(LeaveBalance.query.filter_by(employee_id=emp_user.id).first())
        db.session.delete(LeaveBalance.query.filter_by(employee_id=emp_user.id).first())
        db.session.delete(emp_user)
        db.session.delete(RegistrationRequest.query.get(req_id))
        db.session.delete(RegistrationRequest.query.get(rej_req_id))
        db.session.delete(admin)
        db.session.commit()

        print("PASS: Self-Registration and Approval E2E Workflow")

if __name__ == "__main__":
    run_workflow()
