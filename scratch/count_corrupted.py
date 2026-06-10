import os
import sys

# Adjust path to import from backend
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))

from app import create_app
from extensions import db
from models import Attendance, AttendanceAdjustment

app = create_app()
with app.app_context():
    corrupted_attendance = Attendance.query.filter(Attendance.working_hours < 0).all()
    corrupted_adjustments = AttendanceAdjustment.query.filter(
        AttendanceAdjustment.check_in.isnot(None),
        AttendanceAdjustment.check_out.isnot(None),
        AttendanceAdjustment.check_out <= AttendanceAdjustment.check_in
    ).all()
    
    print(f"CORRUPTED_ATTENDANCE_COUNT: {len(corrupted_attendance)}")
    for r in corrupted_attendance:
        print(f"Attendance ID: {r.id}, Date: {r.date}, In: {r.check_in}, Out: {r.check_out}, Hours: {r.working_hours}")
        
    print(f"CORRUPTED_ADJUSTMENTS_COUNT: {len(corrupted_adjustments)}")
    for r in corrupted_adjustments:
        print(f"Adjustment ID: {r.id}, Date: {r.date}, In: {r.check_in}, Out: {r.check_out}, Status: {r.status}")
