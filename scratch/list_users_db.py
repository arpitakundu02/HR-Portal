import pymysql
import os
from dotenv import load_dotenv

# Load env
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
        cursor.execute("SELECT id, employee_id, name, email, role, is_line_manager, manager_id, is_active FROM users")
        users = cursor.fetchall()
        for u in users:
            print(f"ID: {u['id']} | EmpID: {u['employee_id']} | Name: {u['name']} | Email: {u['email']} | Role: {u['role']} | Manager: {u['is_line_manager']} | MgrID: {u['manager_id']} | Active: {u['is_active']}")
finally:
    db.close()
