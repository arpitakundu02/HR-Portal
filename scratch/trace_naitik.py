import json
from datetime import datetime, timedelta
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))

from app import create_app
from extensions import db
from models import User

def run_trace():
    app = create_app()
    with app.app_context():
        # 1. Query DB
        user = User.query.filter(User.name.like('%Naitik%')).first()
        if not user:
            print("Naitik not found in database!")
            return
            
        print("=== DATABASE RECORD ===")
        print(f"ID: {user.id}")
        print(f"Name: {user.name}")
        print(f"Email: {user.email}")
        print(f"Role: {user.role}")
        print(f"is_line_manager: {user.is_line_manager}")
        print(f"manager_id: {user.manager_id}")
        
        # 2. Simulate API responses
        import jwt
        token = jwt.encode(
            {"user_id": user.id, "role": user.role, "exp": datetime.utcnow() + timedelta(hours=1)},
            app.config["JWT_SECRET_KEY"],
            algorithm="HS256"
        )
        
        client = app.test_client()
        
        print("\n=== API RESPONSE: /api/auth/me ===")
        res_me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
        print(f"Status: {res_me.status_code}")
        print(json.dumps(json.loads(res_me.data), indent=2))
        
        print("\n=== API RESPONSE: /api/team-dashboard/metadata ===")
        res_meta = client.get("/api/team-dashboard/metadata", headers={"Authorization": f"Bearer {token}"})
        print(f"Status: {res_meta.status_code}")
        print(json.dumps(json.loads(res_meta.data), indent=2))
        
        print("\n=== API RESPONSE: /api/hierarchy ===")
        res_hier = client.get("/api/hierarchy", headers={"Authorization": f"Bearer {token}"})
        print(f"Status: {res_hier.status_code}")
        hier_data = json.loads(res_hier.data)
        naitik_node = [n for n in hier_data if n["id"] == user.id]
        print(json.dumps(naitik_node, indent=2))

if __name__ == "__main__":
    run_trace()
