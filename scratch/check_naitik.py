import pymysql

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
        cursor.execute("SELECT id, employee_id, email, name, role, manager_id, is_line_manager, is_active FROM users WHERE name LIKE '%Naitik%'")
        users = cursor.fetchall()
        print("Users matching 'Naitik':")
        for u in users:
            print(u)
            # Find direct reports of this user
            cursor.execute("SELECT id, employee_id, email, name, is_active FROM users WHERE manager_id = %s", (u['id'],))
            reports = cursor.fetchall()
            print(f"  Direct reports ({len(reports)}):")
            for r in reports:
                print(f"    {r}")
except Exception as e:
    print(f"Error: {e}")
finally:
    db.close()
