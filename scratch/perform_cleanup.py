import pymysql

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
        # Get target user ids
        ids = []
        for t in targets:
            cursor.execute("SELECT id, name FROM users WHERE employee_id = %s", (t,))
            row = cursor.fetchone()
            if row:
                ids.append(row)
                
        if not ids:
            print("No target users found to delete.")
            db.close()
            exit(0)
            
        print("=== TARGET USERS TO DELETE ===")
        for user in ids:
            print(f"ID: {user['id']}, Name: {user['name']}")
            
        u_ids = [user['id'] for user in ids]
        
        # Safe deletes of dependent records
        # 1. approvals (where requester or approver is one of these users)
        cursor.execute("DELETE FROM approval_requests WHERE requester_id IN %s OR approver_id IN %s", (tuple(u_ids), tuple(u_ids)))
        print(f"Deleted {cursor.rowcount} approval_requests records.")
        
        # 2. leaves (where employee or responsibility owner is one of these users)
        cursor.execute("DELETE FROM leaves WHERE employee_id IN %s OR responsibility_transfer_id IN %s", (tuple(u_ids), tuple(u_ids)))
        print(f"Deleted {cursor.rowcount} leaves records.")
        
        # 3. attendance
        cursor.execute("DELETE FROM attendance WHERE employee_id IN %s", (tuple(u_ids),))
        print(f"Deleted {cursor.rowcount} attendance records.")
        
        # 4. tasks
        cursor.execute("DELETE FROM tasks WHERE employee_id IN %s OR assigned_by IN %s", (tuple(u_ids), tuple(u_ids)))
        print(f"Deleted {cursor.rowcount} tasks records.")
        
        # 5. timesheets
        cursor.execute("DELETE FROM timesheets WHERE employee_id IN %s", (tuple(u_ids),))
        print(f"Deleted {cursor.rowcount} timesheets records.")
        
        # 6. notifications
        cursor.execute("DELETE FROM notifications WHERE user_id IN %s", (tuple(u_ids),))
        print(f"Deleted {cursor.rowcount} notifications records.")
        
        # 7. leave_balances
        cursor.execute("DELETE FROM leave_balances WHERE employee_id IN %s", (tuple(u_ids),))
        print(f"Deleted {cursor.rowcount} leave_balances records.")
        
        # 8. comp_off_balances
        cursor.execute("DELETE FROM comp_off_balances WHERE employee_id IN %s", (tuple(u_ids),))
        print(f"Deleted {cursor.rowcount} comp_off_balances records.")
        
        # 9. comp_off_requests
        cursor.execute("DELETE FROM comp_off_requests WHERE employee_id IN %s", (tuple(u_ids),))
        print(f"Deleted {cursor.rowcount} comp_off_requests records.")
        
        # 10. users (the targets themselves)
        cursor.execute("DELETE FROM users WHERE id IN %s", (tuple(u_ids),))
        print(f"Deleted {cursor.rowcount} users records.")
        
        db.commit()
        print("[✓] Transaction committed successfully.")
except Exception as e:
    db.rollback()
    print(f"[ERROR] Transaction rolled back: {e}")
finally:
    db.close()
