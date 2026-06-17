import pymysql
import os
import sys
from dotenv import load_dotenv

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))
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
        cursor.execute("SHOW TABLES")
        tables = [list(row.values())[0] for row in cursor.fetchall()]
        
        print("============================================================")
        # 1. Show all foreign key constraints in database
        print("FOREIGN KEY CONSTRAINTS:")
        cursor.execute("""
            SELECT 
                TABLE_NAME, COLUMN_NAME, CONSTRAINT_NAME, REFERENCED_TABLE_NAME, REFERENCED_COLUMN_NAME
            FROM
                INFORMATION_SCHEMA.KEY_COLUMN_USAGE
            WHERE
                REFERENCED_TABLE_SCHEMA = %s
        """, (db_name,))
        constraints = cursor.fetchall()
        for c in constraints:
            print(f"Table: {c['TABLE_NAME']}.{c['COLUMN_NAME']} -> References: {c['REFERENCED_TABLE_NAME']}.{c['REFERENCED_COLUMN_NAME']} (Constraint: {c['CONSTRAINT_NAME']})")
            
        print("\n============================================================")
        # 2. Show structural details for users table
        print("USERS TABLE SCHEMA:")
        cursor.execute("DESCRIBE users")
        for col in cursor.fetchall():
            print(f"Field: {col['Field']} | Type: {col['Type']} | Null: {col['Null']} | Key: {col['Key']} | Default: {col['Default']}")
            
except Exception as e:
    print(f"Error: {e}")
finally:
    db.close()
