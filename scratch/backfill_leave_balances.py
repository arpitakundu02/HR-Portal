import os
import sys

# Adjust path to import from backend
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))

from app import create_app
from extensions import db
from models import User, LeaveBalance

def backfill():
    app = create_app()
    with app.app_context():
        print("[*] Starting backfill of leave balances...")
        
        users = User.query.all()
        for u in users:
            for ltype in ["APL", "WFH"]:
                bal = LeaveBalance.query.filter_by(employee_id=u.id, leave_type=ltype).first()
                gender = u.gender or "Male"
                allocated = 20 if ltype == "APL" else (5 if gender == "Female" else 4)
                
                if not bal:
                    print(f"[+] Creating missing {ltype} balance for {u.name} (ID {u.id})")
                    bal = LeaveBalance(
                        employee_id=u.id,
                        leave_type=ltype,
                        allocated=allocated,
                        used=0,
                        remaining=allocated
                    )
                    db.session.add(bal)
                else:
                    # Update existing record
                    bal.allocated = allocated
                    # Recalculate remaining = allocated - used
                    bal.remaining = bal.allocated - bal.used
                    print(f"[~] Updated {ltype} for {u.name} (ID {u.id}): allocated={bal.allocated}, used={bal.used}, remaining={bal.remaining}")
        
        db.session.commit()
        print("[✓] Backfill completed successfully.")

if __name__ == "__main__":
    backfill()
