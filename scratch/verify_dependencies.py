import pymysql
import json

db = pymysql.connect(
    host="localhost",
    user="root",
    password="AKnk8700",
    database="hr_portal",
    port=3306,
    cursorclass=pymysql.cursors.DictCursor
)

targets = ['HR-003', 'HR-005', 'HR-999']

try:
    with db.cursor() as cursor:
        for emp_id in targets:
            cursor.execute("SELECT id, name, email FROM users WHERE employee_id = %s", (emp_id,))
            user = cursor.fetchone()
            if not user:
                print(f"User {emp_id} not found.")
                continue
                
            u_id = user['id']
            print(f"\n==========================================")
            print(f"DEPENDENCY REPORT FOR {user['name']} ({emp_id})")
            print(f"==========================================")
            
            # 1. Manager check (does anyone report to them?)
            cursor.execute("SELECT count(*) as count FROM users WHERE manager_id = %s", (u_id,))
            print(f"Manager references (direct reports): {cursor.fetchone()['count']}")
            
            # 2. Tasks
            cursor.execute("SELECT count(*) as count FROM tasks WHERE employee_id = %s OR assigned_by = %s", (u_id, u_id))
            print(f"Tasks: {cursor.fetchone()['count']}")
            
            # 3. Meetings
            cursor.execute("SELECT count(*) as count FROM meetings WHERE created_by = %s", (u_id,))
            print(f"Meetings created: {cursor.fetchone()['count']}")
            
            # 4. Approvals (as applicant or actioner)
            cursor.execute("SELECT count(*) as count FROM approval_requests WHERE requester_id = %s OR approver_id = %s", (u_id, u_id))
            print(f"Approvals: {cursor.fetchone()['count']}")
            
            # 5. Attendance
            cursor.execute("SELECT count(*) as count FROM attendance WHERE employee_id = %s", (u_id,))
            print(f"Attendance records: {cursor.fetchone()['count']}")
            
            # 6. Leaves
            cursor.execute("SELECT count(*) as count FROM leaves WHERE employee_id = %s OR responsibility_transfer_id = %s", (u_id, u_id))
            print(f"Leaves / Responsibility transfers: {cursor.fetchone()['count']}")
            
            # 7. Timesheets
            cursor.execute("SELECT count(*) as count FROM timesheets WHERE employee_id = %s", (u_id,))
            print(f"Timesheets: {cursor.fetchone()['count']}")
            
            # 8. Notifications
            cursor.execute("SELECT count(*) as count FROM notifications WHERE user_id = %s", (u_id,))
            print(f"Notifications: {cursor.fetchone()['count']}")
            
except Exception as e:
    print(f"Error: {e}")
finally:
    db.close()
