import pymysql
import os
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '../backend/.env'))

db_host = os.environ.get("DB_HOST", "localhost")
db_user = os.environ.get("DB_USER", "root")
db_pass = os.environ.get("DB_PASSWORD", "AKnk8700")
db_name = os.environ.get("DB_NAME", "hr_portal")
db_port = int(os.environ.get("DB_PORT", 3306))

db = pymysql.connect(
    host=db_host,
    user=db_user,
    password=db_pass,
    database=db_name,
    port=db_port,
    cursorclass=pymysql.cursors.DictCursor
)

try:
    with db.cursor() as cursor:
        cursor.execute("SELECT id, name, department_id FROM users WHERE is_active = 1")
        users = cursor.fetchall()
        print("--- Active Users and their Department IDs ---")
        for u in users:
            print(f"ID: {u['id']} | Name: {u['name']} | DeptID: {u['department_id']}")
            
        cursor.execute("SELECT id, name FROM departments")
        depts = cursor.fetchall()
        print("\n--- Departments ---")
        for d in depts:
            print(f"ID: {d['id']} | Name: {d['name']}")
except Exception as e:
    print(f"Error: {e}")
finally:
    db.close()
