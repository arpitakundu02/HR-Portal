import bcrypt
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
    password_hash = bcrypt.hashpw("Demo@1234".encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    with db.cursor() as cursor:
        cursor.execute("UPDATE users SET password_hash=%s WHERE id=494", (password_hash,))
        db.commit()
        print("[✓] Naitik's password successfully reset to 'Demo@1234'")
finally:
    db.close()
