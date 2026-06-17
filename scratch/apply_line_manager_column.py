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
        print("[*] Adding is_line_manager column to users...")
        cursor.execute("SHOW COLUMNS FROM users LIKE 'is_line_manager'")
        if cursor.rowcount == 0:
            cursor.execute("ALTER TABLE users ADD COLUMN is_line_manager TINYINT(1) NOT NULL DEFAULT 0")
            print("[✓] Added is_line_manager to users.")
        else:
            print("[!] is_line_manager already exists in users. Skipping.")

        db.commit()
        print("[✓] Database schema updated for line manager designation.")
except Exception as e:
    db.rollback()
    print(f"[ERROR] Failed to update schema: {e}")
finally:
    db.close()
