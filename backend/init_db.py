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
        for leave_type in ["APL", "WFH"]:
            balance = LeaveBalance(
                employee_id=admin.id,
                leave_type=leave_type,
                allocated=0,
                used=0,
                remaining=0,
            )
            db.session.add(balance)

        db.session.commit()
        print(f"[✓] Admin account created: {ADMIN_EMAIL} / {ADMIN_PASSWORD}")
        print("     ⚠️  Please change the admin password immediately after first login!")


def seed_settings(app):
    """Insert default system settings if they don't exist."""
    from datetime import datetime
    with app.app_context():
        defaults = {
            "office_latitude": str(app.config.get("OFFICE_LATITUDE", 28.6139)),
            "office_longitude": str(app.config.get("OFFICE_LONGITUDE", 77.2090)),
            "office_radius_meters": str(app.config.get("OFFICE_RADIUS_METERS", 200)),
            "office_updated_by_name": "System Seeder",
            "office_updated_at": datetime.utcnow().isoformat()
        }
        for key, val in defaults.items():
            if not SystemSetting.query.filter_by(key=key).first():
                setting = SystemSetting(key=key, value=val)
                db.session.add(setting)
        db.session.commit()
        print("[✓] Default system settings seeded.")


def main():
    app = create_app()

    with app.app_context():
        print("[*] Creating database tables...")
        db.create_all()
        print("[✓] Tables created.")

    seed_departments(app)
    seed_admin(app)
    seed_settings(app)

    print("\n[✓] Database initialisation complete. You can now start the Flask server.")


if __name__ == "__main__":
    main()
