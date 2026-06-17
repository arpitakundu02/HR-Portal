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
        cursor.execute("SHOW COLUMNS FROM users LIKE 'phone_number'")
        if cursor.rowcount == 0:
            cursor.execute("ALTER TABLE users ADD COLUMN phone_number VARCHAR(20) NULL")
            print("[✓] Added phone_number column to users table.")
        else:
            print("[!] phone_number column already exists.")

        print("[*] Checking resume_update_requests table...")
        cursor.execute("SHOW TABLES LIKE 'resume_update_requests'")
        if cursor.rowcount == 0:
            cursor.execute("""
                CREATE TABLE resume_update_requests (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    employee_id INT NOT NULL,
                    resume_url VARCHAR(255) NOT NULL,
                    status ENUM('Pending', 'Approved', 'Rejected') DEFAULT 'Pending' NOT NULL,
                    approval_request_id INT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (employee_id) REFERENCES users(id) ON DELETE CASCADE,
                    FOREIGN KEY (approval_request_id) REFERENCES approval_requests(id) ON DELETE SET NULL
                )
            """)
            print("[✓] Created resume_update_requests table.")
        else:
            print("[!] resume_update_requests table already exists.")

        db.commit()
except Exception as e:
    db.rollback()
    print(f"[ERROR] Failed to run schema migration: {e}")
finally:
    db.close()
