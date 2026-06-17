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
        print("[*] Checking users table columns...")
        cursor.execute("SHOW COLUMNS FROM users LIKE 'gender'")
        if cursor.rowcount == 0:
            cursor.execute("ALTER TABLE users ADD COLUMN gender VARCHAR(20) DEFAULT 'Male'")
            print("[✓] Added gender column to users table.")
        else:
            print("[!] gender column already exists in users.")

        db.commit()
except Exception as e:
    db.rollback()
    print(f"[ERROR] Failed to run schema migration: {e}")
finally:
    db.close()
