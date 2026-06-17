import os
import sys
import json
from datetime import datetime, timedelta, date

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))

from app import create_app
from extensions import db
from models import User, CompOffRequest, CompOffBalance, Holiday, Attendance, ApprovalRequest, LeaveBalance

def run_workflow():
    app = create_app()
    with app.app_context():
        # Clean up any pre-existing test records to ensure clean run
        User.query.filter(User.employee_id.in_(["TEST-CO-EMP", "TEST-CO-ADM"])).delete()
        # Find candidates to clean
        test_emp = User.query.filter_by(email="test_co_emp@company.com").first()
        if test_emp:
            LeaveBalance.query.filter_by(employee_id=test_emp.id).delete()
            CompOffBalance.query.filter_by(employee_id=test_emp.id).delete()
            CompOffRequest.query.filter_by(employee_id=test_emp.id).delete()
            Attendance.query.filter_by(employee_id=test_emp.id).delete()
            db.session.delete(test_emp)
            
        test_adm = User.query.filter_by(email="test_co_adm@company.com").first()
        if test_adm:
            db.session.delete(test_adm)

        Holiday.query.filter(Holiday.date.in_([date(2026, 6, 7), date(2026, 5, 31)])).delete()
        db.session.commit()

        # Setup test data
        admin = User(
            employee_id="TEST-CO-ADM",
            email="test_co_adm@company.com",
            name="CompOff Admin",
            role="Admin",
            password_hash="hashed"
        )
        db.session.add(admin)
        db.session.commit()

        employee = User(
            employee_id="TEST-CO-EMP",
            email="test_co_emp@company.com",
            name="CompOff Employee",
            role="Employee",
            manager_id=admin.id,
            password_hash="hashed"
        )
        db.session.add(employee)
        db.session.commit()

        # Initialize CompOffBalance
        cob = CompOffBalance(employee_id=employee.id, allocated=0, used=0, remaining=0)
        db.session.add(cob)

        # Set up a holiday on 2026-06-07 (which is a Sunday) and another on 2026-05-31
        h1 = Holiday(name="Sunday Test Holiday", date=date(2026, 6, 7))
        h2 = Holiday(name="Sunday Test Holiday 2", date=date(2026, 5, 31))
        db.session.add_all([h1, h2])

        # Set up Attendance on 2026-06-07 & 2026-05-31 (checked in)
        att1 = Attendance(employee_id=employee.id, date=date(2026, 6, 7), check_in=datetime(2026, 6, 7, 9, 0))
        att2 = Attendance(employee_id=employee.id, date=date(2026, 5, 31), check_in=datetime(2026, 5, 31, 9, 0))
        db.session.add_all([att1, att2])

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

        # 1. Reject future dates
        res_future = client.post("/api/comp-off/request",
                                 headers={"Authorization": f"Bearer {token}"},
                                 data=json.dumps({"date_worked": "2026-06-20", "reason": "Future date work"}),
                                 content_type="application/json")
        assert res_future.status_code == 400, f"Future date was not rejected: {res_future.data}"

        # 2. Reject request if attendance record does not exist
        res_no_att = client.post("/api/comp-off/request",
                                 headers={"Authorization": f"Bearer {token}"},
                                 data=json.dumps({"date_worked": "2026-06-08", "reason": "No attendance check-in"}),
                                 content_type="application/json")
        assert res_no_att.status_code == 400, f"Request without attendance was not rejected: {res_no_att.data}"

        # 3. Reject if not weekend or public holiday
        # Create attendance record for a weekday (e.g. 2026-06-09 is a Tuesday)
        att_weekday = Attendance(employee_id=employee.id, date=date(2026, 6, 9), check_in=datetime(2026, 6, 9, 9, 0))
        db.session.add(att_weekday)
        db.session.commit()

        res_weekday = client.post("/api/comp-off/request",
                                  headers={"Authorization": f"Bearer {token}"},
                                  data=json.dumps({"date_worked": "2026-06-09", "reason": "Normal weekday work"}),
                                  content_type="application/json")
        assert res_weekday.status_code == 400, f"Weekday request was not rejected: {res_weekday.data}"

        # 4. Valid Request submission
        res_valid = client.post("/api/comp-off/request",
                                headers={"Authorization": f"Bearer {token}"},
                                data=json.dumps({"date_worked": "2026-06-07", "reason": "Emergency DB maintenance"}),
                                content_type="application/json")
        assert res_valid.status_code == 201, f"Valid Comp-Off request failed: {res_valid.data}"
        req_id = json.loads(res_valid.data)["request"]["id"]

        # 5. Reject duplicate request for same date
        res_dup = client.post("/api/comp-off/request",
                              headers={"Authorization": f"Bearer {token}"},
                              data=json.dumps({"date_worked": "2026-06-07", "reason": "Duplicate claim"}),
                              content_type="application/json")
        assert res_dup.status_code == 409, f"Duplicate request did not return 409 conflict: {res_dup.status_code}"

        # 6. Verify Approvals Listing contains the request
        res_app_list = client.get("/api/approvals/pending", headers={"Authorization": f"Bearer {admin_token}"})
        assert res_app_list.status_code == 200
        pending_approvals = json.loads(res_app_list.data)
        comp_off_approval = next((a for a in pending_approvals if a["module_type"] == "CompOff" and a["target_id"] == req_id), None)
        assert comp_off_approval is not None, "Comp-Off request not found in pending approvals list"
        
        # Verify target details are polymorphically loaded
        assert comp_off_approval["target_details"]["reason"] == "Emergency DB maintenance"

        # 7. Test Approval Action & Balance updates
        res_action = client.post(f"/api/approvals/{comp_off_approval['id']}/action",
                                 headers={"Authorization": f"Bearer {admin_token}"},
                                 data=json.dumps({"status": "Approved", "comments": "Good work!"}),
                                 content_type="application/json")
        assert res_action.status_code == 200, f"Approval action failed: {res_action.data}"

        # Check balance
        res_bal = client.get("/api/comp-off/balance", headers={"Authorization": f"Bearer {token}"})
        assert res_bal.status_code == 200
        bal_data = json.loads(res_bal.data)
        assert bal_data["allocated"] == 1, f"Balance allocated not updated: {bal_data}"
        assert bal_data["remaining"] == 1, f"Balance remaining not updated: {bal_data}"

        # 8. Test Rejection Workflow
        # Submit second request for 2026-05-31
        res_valid2 = client.post("/api/comp-off/request",
                                 headers={"Authorization": f"Bearer {token}"},
                                 data=json.dumps({"date_worked": "2026-05-31", "reason": "Server monitoring support"}),
                                 content_type="application/json")
        assert res_valid2.status_code == 201
        req_id2 = json.loads(res_valid2.data)["request"]["id"]

        # Action rejection
        res_app_list2 = client.get("/api/approvals/pending", headers={"Authorization": f"Bearer {admin_token}"})
        pending_approvals2 = json.loads(res_app_list2.data)
        comp_off_approval2 = next((a for a in pending_approvals2 if a["module_type"] == "CompOff" and a["target_id"] == req_id2), None)
        
        res_reject = client.post(f"/api/approvals/{comp_off_approval2['id']}/action",
                                 headers={"Authorization": f"Bearer {admin_token}"},
                                 data=json.dumps({"status": "Rejected", "comments": "Invalid proof of active work."}),
                                 content_type="application/json")
        assert res_reject.status_code == 200

        # Verify rejection reason is stored
        req2 = CompOffRequest.query.get(req_id2)
        assert req2.status == "Rejected"
        assert req2.rejection_reason == "Invalid proof of active work."

        # Verify balance remains unchanged (still 1)
        res_bal2 = client.get("/api/comp-off/balance", headers={"Authorization": f"Bearer {token}"})
        bal_data2 = json.loads(res_bal2.data)
        assert bal_data2["allocated"] == 1
        assert bal_data2["remaining"] == 1

        # Clean up database records
        for lb in LeaveBalance.query.filter_by(employee_id=employee.id).all():
            db.session.delete(lb)
        db.session.delete(cob)
        db.session.delete(CompOffRequest.query.get(req_id))
        db.session.delete(CompOffRequest.query.get(req_id2))
        db.session.delete(ApprovalRequest.query.get(comp_off_approval["id"]))
        db.session.delete(ApprovalRequest.query.get(comp_off_approval2["id"]))
        db.session.delete(att1)
        db.session.delete(att2)
        db.session.delete(att_weekday)
        db.session.delete(h1)
        db.session.delete(h2)
        db.session.delete(employee)
        db.session.delete(admin)
        db.session.commit()

        print("PASS: Comp-Off Workflow E2E Validation")

if __name__ == "__main__":
    run_workflow()
