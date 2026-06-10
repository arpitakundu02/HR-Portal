import os
import sys

# Adjust path to import from backend
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))

from app import create_app
from extensions import db
from models import AttendanceAdjustment, Attendance

app = create_app()

def simulate_approval():
    with app.app_context():
        # Load request 7
        req = AttendanceAdjustment.query.get(7)
        if not req:
            print("Adjustment ID 7 not found in database.")
            return
            
        print(f"Initial Status: {req.status}")
        
        # Start a test client request simulation
        client = app.test_client()
        
        # Create a mock admin token
        import jwt
        from datetime import datetime, timedelta
        admin_payload = {"user_id": 2, "role": "Admin"}
        admin_token = jwt.encode(admin_payload, app.config["JWT_SECRET_KEY"], algorithm=app.config["JWT_ALGORITHM"])
        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        
        print("\n--- Simulating Admin POST /api/attendance/regularization/7/action (Approve) ---")
        res = client.post(
            "/api/attendance/regularization/7/action", 
            json={"status": "Approved", "comment": "Trying to approve overnight shift"}, 
            headers=admin_headers
        )
        
        print(f"Response Status Code: {res.status_code}")
        print(f"Response Payload:     {res.get_json()}")
        
        # Expire session and query database again to check persistence
        db.session.expire_all()
        req_after = AttendanceAdjustment.query.get(7)
        print(f"\nDatabase Status After Action: {req_after.status}")
        
        # Check if any attendance record was created for Date 2026-06-08 (Employee ID 7)
        att = Attendance.query.filter_by(employee_id=req.employee_id, date=req.date).first()
        print(f"Attendance record created? {att is not None}")
        if att:
            print(f"   Hours: {att.working_hours}")
            
if __name__ == '__main__':
    simulate_approval()
