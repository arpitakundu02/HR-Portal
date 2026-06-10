# scratch/seed_demo_data.py
import os
import sys
import bcrypt
from datetime import datetime, timedelta, date

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))

from app import create_app
from extensions import db
from models import User, Department, Leave, LeaveBalance, Attendance, Task, Meeting, Announcement, Notification, ApprovalRequest, ApprovalLog, WorkTransferRequest, AttendanceAdjustment

def seed():
    app = create_app()
    with app.app_context():
        print("[*] Starting demo data seeding...")
        
        # 1. Fetch departments
        departments = Department.query.all()
        if not departments:
            print("[!] No departments found. Please run init_db.py first.")
            return
            
        admin = User.query.filter_by(role="Admin").first()
        admin_id = admin.id if admin else 1
        
        # Hash password for all demo users
        password_hash = bcrypt.hashpw("Demo@1234".encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        
        # 2. Create Demo Employees
        demo_names = [
            ("Rohan Sharma", "Tech"),
            ("Aarav Patel", "Research"),
            ("Simran Kaur", "GIS"),
            ("Kabir Singh", "Data Scientist"),
            ("Neha Gupta", "Broker"),
            ("Aditya Verma", "Execution"),
            ("Ishaan Roy", "Account"),
            ("Ananya Sen", "Management"),
            ("Diya Mehta", "Tech"),
            ("Vihaan Rao", "Research")
        ]
        
        users = []
        for i, (name, dept_name) in enumerate(demo_names):
            emp_num = i + 1
            email = f"demo_emp{emp_num:02d}@company.com"
            emp_id = f"DEMO-EMP-{emp_num:02d}"
            
            # Find department
            dept = next((d for d in departments if d.name == dept_name), departments[0])
            
            # Check if user already exists
            existing = User.query.filter_by(email=email).first()
            if existing:
                print(f"[!] User {email} already exists. Skipping user creation.")
                users.append(existing)
                continue
                
            user = User(
                employee_id=emp_id,
                email=email,
                password_hash=password_hash,
                role="Employee",
                name=name,
                fathers_name=f"{name.split()[0]}'s Father",
                dob=date(1990 + (i % 10), 1 + (i % 12), 10 + (i % 18)),
                blood_group="O+" if i % 2 == 0 else "A+",
                address=f"Flat {100 + emp_num}, Sector {10 + emp_num}, City",
                current_address=f"Flat {100 + emp_num}, Sector {10 + emp_num}, City",
                permanent_address=f"Flat {100 + emp_num}, Sector {10 + emp_num}, City",
                emergency_contact=f"+91 98765432{emp_num:02d}",
                department_id=dept.id,
                date_of_joining=date(2022, 1, 15) + timedelta(days=i*10),
                rank="Senior Associate" if i % 3 == 0 else "Associate",
                is_active=True
            )
            db.session.add(user)
            users.append(user)
            
        db.session.commit()
        print(f"[✓] Created {len(users)} demo employees.")
        
        # Link manager hierarchies within demo users
        # Set User 1 and User 8 as managers
        manager_1 = users[0]  # Rohan Sharma
        manager_2 = users[7]  # Ananya Sen
        
        for idx, user in enumerate(users):
            if user.id == manager_1.id or user.id == manager_2.id:
                user.manager_id = admin_id
            else:
                user.manager_id = manager_1.id if idx % 2 == 0 else manager_2.id
                
        # Link departments to managers
        for dept in departments:
            if dept.name in ("Tech", "Data Scientist", "GIS"):
                dept.manager_id = manager_1.id
            else:
                dept.manager_id = manager_2.id
                
        db.session.commit()
        print("[✓] Hierarchies and manager links established.")
        
        # Seed Leave Balances if missing
        for user in users:
            for ltype in ["APL", "WFH"]:
                bal = LeaveBalance.query.filter_by(employee_id=user.id, leave_type=ltype).first()
                if not bal:
                    bal = LeaveBalance(
                        employee_id=user.id,
                        leave_type=ltype,
                        allocated=20 if ltype == "APL" else 15,
                        used=0,
                        remaining=20 if ltype == "APL" else 15
                    )
                    db.session.add(bal)
        db.session.commit()
        
        # 3. Create Attendance Records (Last 15 days)
        today = date.today()
        for offset in range(15):
            record_date = today - timedelta(days=offset)
            # Skip weekends for realistic data
            if record_date.weekday() >= 5:
                continue
                
            for i, user in enumerate(users):
                # Add check-ins for most users, randomly skip some for absenteeism
                if (i + offset) % 10 == 0:
                    continue
                    
                existing = Attendance.query.filter_by(employee_id=user.id, date=record_date).first()
                if existing:
                    continue
                    
                check_in_time = datetime(record_date.year, record_date.month, record_date.day, 9, 0) + timedelta(minutes=i*4 + (offset % 15))
                # For today, leave check_out empty for some users (checked-in state)
                if record_date == today and i % 3 == 0:
                    check_out_time = None
                    hours = 0.0
                else:
                    check_out_time = check_in_time + timedelta(hours=8, minutes=30)
                    hours = 8.5
                    
                att = Attendance(
                    employee_id=user.id,
                    date=record_date,
                    check_in=check_in_time,
                    check_out=check_out_time,
                    working_hours=hours,
                    latitude=28.6139 + (i * 0.0001),
                    longitude=77.2090 + (i * 0.0001)
                )
                db.session.add(att)
        db.session.commit()
        print("[✓] Seeded past attendance logs.")
        
        # 4. Create Leaves
        for i, user in enumerate(users):
            # 2 approved leaves
            l1 = Leave(
                employee_id=user.id,
                leave_type="APL",
                start_date=today - timedelta(days=20 + i),
                end_date=today - timedelta(days=18 + i),
                reason="Family Event",
                status="Approved",
                responsibility_transfer_id=users[(i+1)%len(users)].id
            )
            # 1 pending leave
            l2 = Leave(
                employee_id=user.id,
                leave_type="APL",
                start_date=today + timedelta(days=10 + i),
                end_date=today + timedelta(days=12 + i),
                reason="Medical Checkup",
                status="Pending",
                responsibility_transfer_id=users[(i+1)%len(users)].id
            )
            # 1 rejected leave
            l3 = Leave(
                employee_id=user.id,
                leave_type="WFH",
                start_date=today - timedelta(days=5 + i),
                end_date=today - timedelta(days=4 + i),
                reason="Remote testing",
                status="Rejected",
                responsibility_transfer_id=users[(i+1)%len(users)].id
            )
            db.session.add_all([l1, l2, l3])
        db.session.commit()
        print("[✓] Seeded leaf requests.")
        
        # Update leave balances used/remaining
        for user in users:
            for ltype in ["APL", "WFH"]:
                bal = LeaveBalance.query.filter_by(employee_id=user.id, leave_type=ltype).first()
                if bal:
                    approved_leaves = Leave.query.filter_by(employee_id=user.id, leave_type=ltype, status="Approved").all()
                    used_days = sum((l.end_date - l.start_date).days + 1 for l in approved_leaves)
                    bal.used = used_days
                    bal.remaining = bal.allocated - used_days
        db.session.commit()
        
        # 5. Create Tasks
        for i, user in enumerate(users):
            t1 = Task(
                title=f"Complete Phase {i+1} Documentation",
                description="Review requirements and write comprehensive user guides.",
                employee_id=user.id,
                status="Completed" if i % 2 == 0 else "In Progress",
                due_date=today + timedelta(days=3),
                assigned_by=user.manager_id or admin_id
            )
            t2 = Task(
                title=f"Audit Code Quality for Module {i+1}",
                description="Check for runtime bugs, error boundary handling, and database connection pools.",
                employee_id=user.id,
                status="Pending",
                due_date=today + timedelta(days=10),
                assigned_by=user.manager_id or admin_id
            )
            db.session.add_all([t1, t2])
        db.session.commit()
        print("[✓] Seeded tasks.")
        
        # 6. Create Meetings
        for i, dept in enumerate(departments):
            m1 = Meeting(
                title=f"{dept.name} Weekly Alignment",
                description=f"Weekly sync meeting for {dept.name} department.",
                department_id=dept.id,
                scheduled_at=datetime.utcnow() + timedelta(days=2 + i),
                duration_minutes=45,
                link="https://meet.google.com/abc-def-ghi",
                created_by=admin_id
            )
            db.session.add(m1)
        # Add a couple of company-wide meetings
        m_company = Meeting(
            title="Q3 Town Hall & Roadmap",
            description="Company-wide updates and Q3 milestones review.",
            department_id=None,
            scheduled_at=datetime.utcnow() + timedelta(days=5),
            duration_minutes=60,
            link="https://meet.google.com/xyz-pdq-rst",
            created_by=admin_id
        )
        db.session.add(m_company)
        db.session.commit()
        print("[✓] Seeded department and company-wide meetings.")
        
        # 7. Create Announcements
        a1 = Announcement(
            title="HR Portal Upgrade Complete!",
            content="We have successfully upgraded the notification infrastructure and redesigned the check-in panel.",
            audience_type="All",
            created_by=admin_id,
            is_active=True
        )
        a2 = Announcement(
            title="Policy Update: Regularization limits",
            content="Starting this month, employees are restricted to a maximum of 4 attendance regularization requests per month.",
            audience_type="All",
            created_by=admin_id,
            is_active=True
        )
        db.session.add_all([a1, a2])
        db.session.commit()
        print("[✓] Seeded announcements.")
        
        # 8. Create Notifications
        for user in users:
            n1 = Notification(
                user_id=user.id,
                title="Welcome to HR Portal",
                content="Explore your new dashboard, leave balances, and tasks.",
                is_read=True,
                notification_type="System",
                action_url="/"
            )
            n2 = Notification(
                user_id=user.id,
                title="Assigned New Task",
                content="You have been assigned the code quality audit task.",
                is_read=False,
                notification_type="Task",
                action_url="/tasks"
            )
            db.session.add_all([n1, n2])
        db.session.commit()
        print("[✓] Seeded in-app notifications.")
        
        # 9. Create Work Transfer Request & Approvals
        for i in range(3):
            requester = users[i*2]
            delegate = users[i*2 + 1]
            wt = WorkTransferRequest(
                requester_id=requester.id,
                delegate_to_id=delegate.id,
                start_date=today - timedelta(days=2),
                end_date=today + timedelta(days=5),
                transfer_tasks=True,
                transfer_approvals=True,
                transfer_meetings=True,
                status="Approved"
            )
            db.session.add(wt)
            db.session.flush()
            
            # Create matching ApprovalRequest
            app_req = ApprovalRequest(
                requester_id=requester.id,
                approver_id=requester.manager_id or admin_id,
                module_type="WorkTransfer",
                target_id=wt.id,
                status="Approved"
            )
            db.session.add(app_req)
            db.session.flush()
            
            wt.approval_request_id = app_req.id
            
            # Log entry
            log = ApprovalLog(
                approval_request_id=app_req.id,
                actioner_id=requester.manager_id or admin_id,
                old_status="Pending",
                new_status="Approved",
                comments="Delegation verified."
            )
            db.session.add(log)
            
        db.session.commit()
        print("[✓] Seeded work transfers and approvals.")
        print("[✓] Demo seeding completed successfully!")

if __name__ == "__main__":
    seed()
