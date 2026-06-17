import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))

from app import create_app
from extensions import db
from models import User, Announcement, Policy

def create_items():
    app = create_app()
    with app.app_context():
        # Get admin user
        admin = User.query.filter_by(role="Admin").first()
        if not admin:
            print("No Admin user found to associate as creator/updater.")
            return

        # 1. Create a test announcement
        ann = Announcement(
            title="Test Announcement",
            content="This is a test announcement to verify manual rendering.",
            audience_type="All",
            created_by=admin.id,
            is_active=True
        )
        db.session.add(ann)
        db.session.commit()
        print(f"Created Announcement with ID: {ann.id}")

        # 2. Create a test policy
        policy = Policy(
            title="Test Policy",
            description="This is a test policy to verify manual rendering.",
            category="Leave Policy",
            is_latest=True,
            version=1,
            updated_by=admin.id
        )
        db.session.add(policy)
        db.session.commit()
        
        # Set group ID to self ID
        policy.policy_group_id = policy.id
        db.session.commit()
        print(f"Created Policy with ID: {policy.id}")

if __name__ == "__main__":
    create_items()
