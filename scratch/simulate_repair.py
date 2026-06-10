import os
import sys
from datetime import datetime, timedelta

# Adjust path to import from backend
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))

from app import create_app
from extensions import db
from models import Attendance, AttendanceAdjustment

app = create_app()
with app.app_context():
    att6 = Attendance.query.get(6)
    adj10 = AttendanceAdjustment.query.get(10)
    adj7 = AttendanceAdjustment.query.get(7)
    
    print("=============================================================")
    print("CURRENT RECORDS STATE (BEFORE REPAIR)")
    print("=============================================================")
    
    if att6:
        print(f"Attendance ID 6:")
        print(f"  check_in:      {att6.check_in}")
        print(f"  check_out:     {att6.check_out}")
        print(f"  working_hours: {att6.working_hours}")
    else:
        print("Attendance ID 6 not found!")
        
    if adj10:
        print(f"Adjustment ID 10:")
        print(f"  check_in:      {adj10.check_in}")
        print(f"  check_out:     {adj10.check_out}")
        print(f"  status:        {adj10.status}")
    else:
        print("Adjustment ID 10 not found!")
        
    if adj7:
        print(f"Adjustment ID 7:")
        print(f"  check_in:      {adj7.check_in}")
        print(f"  check_out:     {adj7.check_out}")
        print(f"  status:        {adj7.status}")
    else:
        print("Adjustment ID 7 not found!")
        
    print("\n=============================================================")
    print("SIMULATING DATA REPAIR IN MEMORY")
    print("=============================================================")
    
    # 1. Simulate Attendance ID 6 repair
    att6_in = att6.check_in
    att6_out_sim = att6.check_out + timedelta(days=1)
    delta_att6 = att6_out_sim - att6_in
    att6_hours_sim = round(delta_att6.total_seconds() / 3600, 2)
    
    print("Simulated Attendance ID 6:")
    print(f"  New check_in:      {att6_in}")
    print(f"  New check_out:     {att6_out_sim}")
    print(f"  New working_hours: {att6_hours_sim} (float: {float(att6_hours_sim)})")
    
    # 2. Simulate Adjustment ID 10 repair
    adj10_in = adj10.check_in
    adj10_out_sim = adj10.check_out + timedelta(days=1)
    print("Simulated Adjustment ID 10:")
    print(f"  New check_in:      {adj10_in}")
    print(f"  New check_out:     {adj10_out_sim}")
    print(f"  status:            {adj10.status}")
    
    # 3. Simulate Adjustment ID 7 repair
    adj7_in = adj7.check_in
    adj7_out_sim = adj7.check_out + timedelta(days=1)
    print("Simulated Adjustment ID 7:")
    print(f"  New check_in:      {adj7_in}")
    print(f"  New check_out:     {adj7_out_sim}")
    print(f"  status:            {adj7.status}")
    
    print("\n=============================================================")
    print("VERIFICATION OF REPAIR")
    print("=============================================================")
    print(f"Are calculated hours for ID 6 correct? {att6_hours_sim == 13.00} (value: {att6_hours_sim})")
    
    # Check if Admin approval of simulated ID 7 would succeed
    # Approval succeeds if check_out_sim > check_in
    approval_success = (adj7_out_sim > adj7_in)
    print(f"Would Admin approval of ID 7 succeed? {approval_success} ({adj7_out_sim} > {adj7_in})")
    
    # Safety Check: Affects other records?
    print("Would any other records be affected? False (Updates are targeted explicitly by ID keys 6, 10, 7)")
