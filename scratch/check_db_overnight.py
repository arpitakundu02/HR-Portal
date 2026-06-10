import os
import sys

# Adjust path to import from backend
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))

from app import create_app
from extensions import db
from models import Attendance

app = create_app()
with app.app_context():
    records = Attendance.query.all()
    print(f"Total attendance records: {len(records)}")
    for r in records:
        print(f"ID: {r.id}, Date: {r.date}, Check-in: {r.check_in}, Check-out: {r.check_out}, Working Hours: {r.working_hours}")
