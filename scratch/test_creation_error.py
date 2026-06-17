import os
import sys
import json
from datetime import datetime, timedelta

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))

from app import create_app
from extensions import db
from models import User, Announcement

def test_creation():
    app = create_app()
    with app.app_context():
        admin = User.query.filter_by(role="Admin").first()
        if not admin:
            admin = User(
                employee_id="TEST-ADM-999",
                email="admin@company.com",
                name="Admin User",
                role="Admin",
                password_hash="hashed"
            )
            db.session.add(admin)
            db.session.commit()

        import jwt
        admin_token = jwt.encode(
            {"user_id": admin.id, "role": "Admin", "exp": datetime.utcnow() + timedelta(hours=1)},
            app.config["JWT_SECRET_KEY"],
            algorithm="HS256"
        )

        client = app.test_client()

        # Test posting form data (multipart/form-data)
        data = {
            "title": "Form Announcement",
            "content": "Content of form announcement",
            "audience_type": "All",
            "is_active": "true"
        }
        res = client.post(
            "/api/announcements/",
            headers={"Authorization": f"Bearer {admin_token}"},
            data=data
        )
        print("Multipart Status Code:", res.status_code)
        print("Multipart Response:", res.data.decode())

        # Test posting JSON with is_active as string 'true'
        data_json = {
            "title": "JSON Announcement",
            "content": "Content of json announcement",
            "audience_type": "All",
            "is_active": "true"
        }
        res_json = client.post(
            "/api/announcements/",
            headers={"Authorization": f"Bearer {admin_token}"},
            data=json.dumps(data_json),
            content_type="application/json"
        )
        print("JSON Status Code:", res_json.status_code)
        print("JSON Response:", res_json.data.decode())

if __name__ == "__main__":
    test_creation()
