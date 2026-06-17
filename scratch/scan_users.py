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

try:
    with db.cursor() as cursor:
        cursor.execute("SELECT id, employee_id, email, name, role, is_line_manager, created_at FROM users ORDER BY id ASC")
        users = cursor.fetchall()
        print("=== DATABASE USERS ===")
        for u in users:
            # Format datetime
            u['created_at'] = u['created_at'].isoformat()
            print(json.dumps(u))
except Exception as e:
    print(f"Error: {e}")
finally:
    db.close()
