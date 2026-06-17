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
        print("=== Naitik's User Record ===")
        cursor.execute("SELECT * FROM users WHERE id=494")
        print(cursor.fetchone())
        
        print("\n=== Resume Update Requests for Employee 494 ===")
        cursor.execute("SELECT * FROM resume_update_requests WHERE employee_id=494")
        print(cursor.fetchall())
        
        print("\n=== Approval Requests for Requester 494 ===")
        cursor.execute("SELECT * FROM approval_requests WHERE requester_id=494")
        print(cursor.fetchall())
finally:
    db.close()
