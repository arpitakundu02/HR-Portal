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
        print("[*] Checking announcements table columns...")
        cursor.execute("SHOW COLUMNS FROM announcements LIKE 'attachment_url'")
        if cursor.rowcount == 0:
            cursor.execute("ALTER TABLE announcements ADD COLUMN attachment_url VARCHAR(255) NULL")
            print("[✓] Added attachment_url column to announcements table.")
        else:
            print("[!] attachment_url column already exists in announcements.")

        print("[*] Checking policies table...")
        cursor.execute("SHOW TABLES LIKE 'policies'")
        if cursor.rowcount == 0:
            cursor.execute("""
                CREATE TABLE policies (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    policy_group_id INT NULL,
                    version INT NOT NULL DEFAULT 1,
                    is_latest BOOLEAN NOT NULL DEFAULT TRUE,
                    title VARCHAR(255) NOT NULL,
                    description TEXT NOT NULL,
                    category ENUM(
                        'Leave Policy',
                        'Attendance Policy',
                        'WFH Policy',
                        'Comp-Off Policy',
                        'Code of Conduct',
                        'Security Guidelines',
                        'Employee Handbook'
                    ) NOT NULL,
                    attachment_url VARCHAR(255) NULL,
                    updated_by INT NULL,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (updated_by) REFERENCES users(id) ON DELETE SET NULL
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """)
            print("[✓] Created policies table.")
        else:
            print("[!] policies table already exists.")

        db.commit()
except Exception as e:
    db.rollback()
    print(f"[ERROR] Failed to run schema migration: {e}")
finally:
    db.close()
