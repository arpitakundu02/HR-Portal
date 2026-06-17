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
        print("[*] Updating existing demo employee genders...")
        female_names = ["Simran Kaur", "Neha Gupta", "Ananya Sen", "Diya Mehta"]
        
        for name in female_names:
            cursor.execute("UPDATE users SET gender = 'Female' WHERE name = %s", (name,))
            print(f"[✓] Updated {name} to Female. (rows affected: {cursor.rowcount})")
            
        cursor.execute("UPDATE users SET gender = 'Male' WHERE email LIKE 'demo_emp%%' AND name NOT IN (%s, %s, %s, %s)", tuple(female_names))
        print(f"[✓] Set other demo employees to Male. (rows affected: {cursor.rowcount})")
        
        db.commit()
except Exception as e:
    db.rollback()
    print(f"[ERROR] Failed to update demo genders: {e}")
finally:
    db.close()
