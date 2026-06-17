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
        cursor.execute("SELECT id, name, department_id, is_active FROM users WHERE id=4")
        user = cursor.fetchone()
        print("User 4 (Aradhya):", user)
        
        cursor.execute("SELECT id, name, department_id, is_active FROM users WHERE department_id=2")
        tech_users = cursor.fetchall()
        print("Tech Users (Dept 2) in DB:", tech_users)
        
        cursor.execute("SELECT id, name, department_id, is_active FROM users WHERE is_active=1 AND department_id=2")
        active_tech_users = cursor.fetchall()
        print("Active Tech Users in DB:", active_tech_users)
finally:
    db.close()
