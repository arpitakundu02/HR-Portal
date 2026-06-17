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
        cursor.execute("SHOW COLUMNS FROM users LIKE 'photo_url'")
        if cursor.rowcount == 0:
            cursor.execute("ALTER TABLE users ADD COLUMN photo_url VARCHAR(255) NULL")
            print("[✓] Added photo_url column to users table.")
        else:
            print("[!] photo_url column already exists. Skipping.")
        db.commit()
except Exception as e:
    db.rollback()
    print(f"[ERROR] Failed to modify table users: {e}")
finally:
    db.close()
