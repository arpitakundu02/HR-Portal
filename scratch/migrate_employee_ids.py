import pymysql
import os
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '../backend/.env'))

db_host = os.environ.get("DB_HOST", "localhost")
db_user = os.environ.get("DB_USER", "root")
db_pass = os.environ.get("DB_PASSWORD", "AKnk8700")
db_name = os.environ.get("DB_NAME", "hr_portal")
db_port = int(os.environ.get("DB_PORT", 3306))

DEPT_PREFIXES = {
    "Research": "RES",
    "Tech": "TECH",
    "GIS": "GIS",
    "Management": "MGT",
    "Data Scientist": "DATA",
    "Broker": "BRK",
    "Execution": "EXEC",
    "Account": "ACC",
    "HR": "HR"
}

def get_db_connection():
    return pymysql.connect(
        host=db_host,
        user=db_user,
        password=db_pass,
        database=db_name,
        port=db_port,
        cursorclass=pymysql.cursors.DictCursor
    )

def migrate():
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # Fetch all users and their departments
            cursor.execute("""
                SELECT u.id, u.employee_id, u.name, u.role, d.name AS dept_name 
                FROM users u
                LEFT JOIN departments d ON u.department_id = d.id
                ORDER BY u.id ASC
            """)
            users = cursor.fetchall()
            
            # Group users by department prefix
            dept_groups = {}
            for u in users:
                dept_name = u["dept_name"]
                # If no department (e.g. root Admin), keep their current ID as is
                if not dept_name:
                    continue
                prefix = DEPT_PREFIXES.get(dept_name)
                if not prefix:
                    prefix = "EMP" # generic fallback if department not in predefined list
                dept_groups.setdefault(prefix, []).append(u)
            
            # Compute mappings
            computed_mappings = []
            update_queries = []
            
            for prefix, group in dept_groups.items():
                for idx, u in enumerate(group):
                    seq = idx + 1
                    new_id = f"{prefix}-{seq:03d}"
                    computed_mappings.append({
                        "id": u["id"],
                        "old_id": u["employee_id"],
                        "new_id": new_id,
                        "name": u["name"],
                        "dept_name": u["dept_name"] or "None"
                    })
                    update_queries.append((new_id, u["id"]))
            
            # Apply mappings to DB
            print("Applying employee ID updates...")
            for new_id, user_id in update_queries:
                cursor.execute("UPDATE users SET employee_id=%s WHERE id=%s", (new_id, user_id))
            conn.commit()
            print("[✓] Migration successfully committed to database.")
            
            # Print report
            print("\n=== EMPLOYEE ID MIGRATION REPORT ===")
            print(f"{'OLD ID':<15} | {'NEW ID':<15} | {'NAME':<20} | {'DEPARTMENT':<20}")
            print("-" * 78)
            for m in computed_mappings:
                print(f"{m['old_id']:<15} | {m['new_id']:<15} | {m['name']:<20} | {m['dept_name']:<20}")
                
    except Exception as e:
        conn.rollback()
        print(f"Error during migration: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
