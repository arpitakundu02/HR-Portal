import os
import sys
from datetime import datetime, timedelta

# Adjust path to import from backend
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))

from app import create_app
from extensions import db
from models import Attendance, AttendanceAdjustment

app = create_app()

def execute_repair():
    print("=============================================================")
    print("EXECUTING TARGETED DATABASE DATA REPAIR")
    print("=============================================================")
    
    with app.app_context():
        # Begin transaction
        try:
            # 1. Repair Attendance ID 6
            att6 = Attendance.query.get(6)
            if att6:
                # Idempotency check: only add a day if it is still recorded on the same date
                if att6.check_out.date() == att6.check_in.date():
                    print(f"[+] Repairing Attendance ID 6 (Current Hours: {att6.working_hours})...")
                    att6.check_out += timedelta(days=1)
                    att6.calculate_hours()
                    print(f"    Attendance ID 6 fixed. New check_out: {att6.check_out}, New Hours: {att6.working_hours}")
                else:
                    print(f"[~] Attendance ID 6 already processed. Skipped. (Current check_out: {att6.check_out})")
            else:
                print("[-] Attendance ID 6 not found in database.")

            # 2. Repair AttendanceAdjustment ID 10
            adj10 = AttendanceAdjustment.query.get(10)
            if adj10:
                if adj10.check_out.date() == adj10.check_in.date():
                    print("[+] Repairing Approved Adjustment ID 10...")
                    adj10.check_out += timedelta(days=1)
                    print(f"    Adjustment ID 10 fixed. New check_out: {adj10.check_out}")
                else:
                    print(f"[~] Adjustment ID 10 already processed. Skipped. (Current check_out: {adj10.check_out})")
            else:
                print("[-] Adjustment ID 10 not found in database.")

            # 3. Repair AttendanceAdjustment ID 7
            adj7 = AttendanceAdjustment.query.get(7)
            if adj7:
                if adj7.check_out.date() == adj7.check_in.date():
                    print("[+] Repairing Pending Adjustment ID 7...")
                    adj7.check_out += timedelta(days=1)
                    print(f"    Adjustment ID 7 fixed. New check_out: {adj7.check_out}")
                else:
                    print(f"[~] Adjustment ID 7 already processed. Skipped. (Current check_out: {adj7.check_out})")
            else:
                print("[-] Adjustment ID 7 not found in database.")

            # Commit the transaction
            db.session.commit()
            print("\n[✓] Database updates committed successfully!")
            
            # 4. Post-Commit Re-Query Verification
            print("\n=== POST-COMMIT VERIFICATION ===")
            db.session.expire_all()  # Force reload from database
            
            v_att6 = Attendance.query.get(6)
            v_adj10 = AttendanceAdjustment.query.get(10)
            v_adj7 = AttendanceAdjustment.query.get(7)
            
            if v_att6:
                print(f"Verified Attendance ID 6: check_out={v_att6.check_out}, working_hours={v_att6.working_hours}")
                assert v_att6.working_hours == 13.00, f"Error: Hours should be 13.00, got {v_att6.working_hours}"
            if v_adj10:
                print(f"Verified Adjustment ID 10: check_out={v_adj10.check_out}, status={v_adj10.status}")
                assert v_adj10.check_out.day == 7, "Error: Adjustment 10 checkout day should be 7"
            if v_adj7:
                print(f"Verified Adjustment ID 7: check_out={v_adj7.check_out}, status={v_adj7.status}")
                assert v_adj7.check_out.day == 9, "Error: Adjustment 7 checkout day should be 9"
            print("[✓] Post-commit validation check successful!")
            
        except Exception as e:
            db.session.rollback()
            print(f"\n[🛑] ERROR encountered during repair: {e}. Transaction rolled back.")
            raise

if __name__ == '__main__':
    execute_repair()
