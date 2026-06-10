import os
import sys

# Adjust path to import from backend
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))

from app import create_app
from extensions import db
from models import Attendance, AttendanceAdjustment

app = create_app()
with app.app_context():
    att = Attendance.query.get(6)
    adj = AttendanceAdjustment.query.get(10)
    
    print("=== RECORD DETAILS ===")
    if att:
        print(f"Attendance ID 6: Date={att.date}, EmployeeID={att.employee_id}, CheckIn={att.check_in}, CheckOut={att.check_out}, Hours={att.working_hours}")
    else:
        print("Attendance ID 6 not found")
        
    if adj:
        print(f"Adjustment ID 10: Date={adj.date}, EmployeeID={adj.employee_id}, CheckIn={adj.check_in}, CheckOut={adj.check_out}, Status={adj.status}, ActionedBy={adj.actioned_by}")
    else:
        print("Adjustment ID 10 not found")
        
    print("\n=== VERIFICATION ===")
    if att and adj:
        match_in = (att.check_in == adj.check_in)
        match_out = (att.check_out == adj.check_out)
        match_emp = (att.employee_id == adj.employee_id)
        match_date = (att.date == adj.date)
        print(f"1. Do check_in values match? {match_in} ({att.check_in} vs {adj.check_in})")
        print(f"2. Do check_out values match? {match_out} ({att.check_out} vs {adj.check_out})")
        print(f"3. Do employee IDs match? {match_emp}")
        print(f"4. Do dates match? {match_date}")
        
        # Test calculation
        from datetime import timedelta
        test_out = adj.check_out + timedelta(days=1)
        test_delta = test_out - adj.check_in
        test_hours = round(test_delta.total_seconds() / 3600, 2)
        print(f"5. Calculated hours after +1 day to checkout: {test_hours} (Expected: 13.00)")
        
    # Check other attendance records referencing same adjustment date/employee
    if adj:
        other_att = Attendance.query.filter(Attendance.employee_id == adj.employee_id, Attendance.date == adj.date, Attendance.id != 6).all()
        print(f"6. Count of other attendance rows matching same date/employee: {len(other_att)}")
        
    # Scan for ANY other records with negative hours in the entire database
    all_neg_att = Attendance.query.filter(Attendance.working_hours < 0).all()
    print(f"7. Any other attendance records with working_hours < 0? {len(all_neg_att) > 1} (Total negative count including ID 6: {len(all_neg_att)})")
    for r in all_neg_att:
        if r.id != 6:
            print(f"   Extra Corrupted Row -> ID: {r.id}, Date: {r.date}, Hours: {r.working_hours}")
            
    # Check if there are other approved adjustments with check_out <= check_in
    all_corrupt_adj = AttendanceAdjustment.query.filter(
        AttendanceAdjustment.check_in.isnot(None),
        AttendanceAdjustment.check_out.isnot(None),
        AttendanceAdjustment.check_out <= AttendanceAdjustment.check_in
    ).all()
    print(f"8. Approved adjustments with check_out <= check_in (excl ID 10):")
    for r in all_corrupt_adj:
        if r.id != 10:
            print(f"   Extra Corrupted Adjustment -> ID: {r.id}, Date: {r.date}, Status: {r.status}, In: {r.check_in}, Out: {r.check_out}")
