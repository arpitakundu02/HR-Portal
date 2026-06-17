# scratch/e2e_hierarchy.py
import os
import sys
import json
from datetime import datetime, timedelta

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))

from app import create_app
from extensions import db
from models import User

def run_workflow():
    app = create_app()
    with app.app_context():
        # Setup test data
        admin = User(
            employee_id="TEST-HCY-ADM",
            email="hcy_admin@company.com",
            name="HCY Admin",
            role="Admin",
            password_hash="hashed"
        )
        supervisor = User(
            employee_id="TEST-HCY-SUP",
            email="hcy_super@company.com",
            name="HCY Supervisor",
            role="Employee",
            password_hash="hashed"
        )
        db.session.add_all([admin, supervisor])
        db.session.commit()

        # Employee reporting to Supervisor
        employee = User(
            employee_id="TEST-HCY-EMP",
            email="hcy_emp@company.com",
            name="HCY Employee",
            role="Employee",
            manager_id=supervisor.id,
            password_hash="hashed"
        )
        db.session.add(employee)
        db.session.commit()

        # Generate JWT client token
        import jwt
        token = jwt.encode(
            {"user_id": employee.id, "role": "Employee", "exp": datetime.utcnow() + timedelta(hours=1)},
            app.config["JWT_SECRET_KEY"],
            algorithm="HS256"
        )

        client = app.test_client()

        # Query /api/hierarchy
        res = client.get("/api/hierarchy", headers={"Authorization": f"Bearer {token}"})
        assert res.status_code == 200, f"Hierarchy retrieval failed: {res.data}"
        nodes = json.loads(res.data)
        
        # Verify reports and structures
        node_map = {n["employee_id"]: n for n in nodes}
        assert "TEST-HCY-ADM" in node_map
        assert "TEST-HCY-SUP" in node_map
        assert "TEST-HCY-EMP" in node_map

        emp_node = node_map["TEST-HCY-EMP"]
        assert emp_node["manager_id"] == supervisor.id
        assert emp_node["manager_name"] == "HCY Supervisor"

        # Cleanup
        db.session.delete(employee)
        db.session.delete(supervisor)
        db.session.delete(admin)
        db.session.commit()

        print("PASS: Organization Hierarchy & Tree API Verification")

if __name__ == "__main__":
    run_workflow()
