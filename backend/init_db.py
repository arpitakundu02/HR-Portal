"""
backend/init_db.py
-------------------
Database initialisation script.

Run ONCE after setting up MySQL to:
  1. Create all tables from SQLAlchemy models.
  2. Seed the 8 default departments.
  3. Create the default Admin account.

Usage:
    python init_db.py

IMPORTANT: Set DB_PASSWORD in your .env file before running.
"""

import bcrypt
from app import create_app
from extensions import db
from models import Department, User, LeaveBalance, SystemSetting, AttendanceAdjustment

# Default departments defined in the requirements
DEFAULT_DEPARTMENTS = [
    ("Research",       "Research and Innovation Department"),
    ("Tech",           "Technology and Engineering Department"),
    ("GIS",            "Geographic Information Systems Department"),
    ("Data Scientist", "Data Science and Analytics Department"),
    ("Broker",         "Brokerage Services Department"),
    ("Execution",      "Operations and Execution Department"),
    ("Account",        "Accounts and Finance Department"),
    ("Management",     "Senior Management Department"),
]

# Default Admin credentials (change after first login!)
ADMIN_EMAIL = "admin@hrportal.com"
ADMIN_PASSWORD = "Admin@1234"
ADMIN_NAME = "System Administrator"


def seed_departments(app):
    """Insert default departments if they don't exist."""
    with app.app_context():
        for name, description in DEFAULT_DEPARTMENTS:
            if not Department.query.filter_by(name=name).first():
                dept = Department(name=name, description=description)
                db.session.add(dept)
        db.session.commit()
        print(f"[✓] {len(DEFAULT_DEPARTMENTS)} departments seeded.")


def seed_admin(app):
    """Create the default Admin account if it doesn't exist."""
    with app.app_context():
        if User.query.filter_by(email=ADMIN_EMAIL).first():
            print(f"[!] Admin account '{ADMIN_EMAIL}' already exists. Skipping.")
            return

        pw_hash = bcrypt.hashpw(ADMIN_PASSWORD.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

        admin = User(
            employee_id="HR-ADMIN",
            email=ADMIN_EMAIL,
            password_hash=pw_hash,
            role="Admin",
            name=ADMIN_NAME,
        )
        db.session.add(admin)
        db.session.flush()

        # Create leave balances for admin too
        db.session.add(LeaveBalance(
            employee_id=admin.id,
            leave_type="APL",
            allocated=20,
            used=0,
            remaining=20,
        ))
        db.session.add(LeaveBalance(
            employee_id=admin.id,
            leave_type="WFH",
            allocated=4, # Admin defaults to Male
            used=0,
            remaining=4,
        ))

        db.session.commit()
        print(f"[✓] Admin account created: {ADMIN_EMAIL} / {ADMIN_PASSWORD}")
        print("     ⚠️  Please change the admin password immediately after first login!")


def seed_settings(app):
    """Insert default system settings if they don't exist."""
    from datetime import datetime
    with app.app_context():
        defaults = {
            "company_name": "HR Portal Inc.",
            "company_email": "info@hrportal.com",
            "company_phone": "+1 555-0199",
            "company_address": "123 Tech Avenue, Silicon Valley, CA",
            "apl_allocation": "20",
            "wfh_limit_male": "4",
            "wfh_limit_female": "5",
            "office_latitude": str(app.config.get("OFFICE_LATITUDE", 28.6139)),
            "office_longitude": str(app.config.get("OFFICE_LONGITUDE", 77.2090)),
            "office_radius_meters": str(app.config.get("OFFICE_RADIUS_METERS", 200)),
            "standard_working_hours": "9",
            "min_password_length": "8",
            "session_timeout": "30",
            "enable_self_registration": "true",
            "enable_email_notifications": "true",
            "enable_attendance_reminders": "true",
            "enable_leave_approval_emails": "true",
            "office_updated_by_name": "System Seeder",
            "office_updated_at": datetime.utcnow().isoformat()
        }
        for key, val in defaults.items():
            if not SystemSetting.query.filter_by(key=key).first():
                setting = SystemSetting(key=key, value=val)
                db.session.add(setting)
        db.session.commit()
        print("[✓] Default system settings seeded.")


def seed_policies(app):
    """Seed default policies if Policies table is empty."""
    with app.app_context():
        from models import Policy
        if Policy.query.count() == 0:
            from routes.policies import seed_default_policies
            try:
                seed_default_policies()
                print("[✓] Default company policies seeded.")
            except Exception as e:
                print(f"[!] Failed to seed policies: {e}")


def run_migrations(app):
    """Run alter queries to add deleted_at and deleted_by to users table if they don't exist."""
    from sqlalchemy import text
    with app.app_context():
        try:
            db.session.execute(text("ALTER TABLE users ADD COLUMN deleted_at DATETIME NULL"))
            db.session.commit()
            print("[✓] Column 'deleted_at' added to 'users' table.")
        except Exception:
            db.session.rollback()

        try:
            db.session.execute(text("ALTER TABLE users ADD COLUMN deleted_by INT NULL"))
            db.session.commit()
            db.session.execute(text("ALTER TABLE users ADD CONSTRAINT fk_users_deleted_by FOREIGN KEY (deleted_by) REFERENCES users(id) ON DELETE SET NULL"))
            db.session.commit()
            print("[✓] Column 'deleted_by' added to 'users' table.")
        except Exception:
            db.session.rollback()


def main():
    app = create_app()

    with app.app_context():
        print("[*] Creating database tables...")
        db.create_all()
        print("[✓] Tables created.")

    run_migrations(app)
    seed_departments(app)
    seed_admin(app)
    seed_settings(app)
    seed_policies(app)

    print("\n[✓] Database initialisation complete. You can now start the Flask server.")


if __name__ == "__main__":
    main()
