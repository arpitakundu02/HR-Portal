import os
import pymysql
import sys
from dotenv import load_dotenv

# Adjust path to import Flask app
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))
from app import create_app
from extensions import db
from models import Holiday

def get_db_connection():
    env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend', '.env'))
    load_dotenv(env_path)
    return pymysql.connect(
        host=os.environ.get("DB_HOST", "localhost"),
        user=os.environ.get("DB_USER", "root"),
        password=os.environ.get("DB_PASSWORD", ""),
        database=os.environ.get("DB_NAME", "hr_portal"),
        port=int(os.environ.get("DB_PORT", "3306")),
        cursorclass=pymysql.cursors.DictCursor
    )

def main():
    print("--- STEP 1: INITIAL STATE ---")
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) AS count FROM holidays WHERE YEAR(date) = 2027")
            count_2027_before = cursor.fetchone()['count']
            print(f"Holidays for 2027 in live DB before simulation: {count_2027_before}")
            
            print("\n--- STEP 2: SIMULATE EMPTY STATE FOR 2027 ---")
            cursor.execute("DELETE FROM holidays WHERE YEAR(date) = 2027")
            conn.commit()
            print("Deleted all 2027 holidays from the live database.")
            
            cursor.execute("SELECT COUNT(*) AS count FROM holidays WHERE YEAR(date) = 2027")
            count_2027_cleared = cursor.fetchone()['count']
            print(f"Holidays for 2027 in live DB now: {count_2027_cleared}")
    finally:
        conn.close()

    print("\n--- STEP 3: SIMULATE OPENING HOLIDAYS PAGE ---")
    # Set up Flask App Context with actual DB config
    app = create_app()
    with app.app_context():
        # Create a test client to execute GET /api/holidays
        client = app.test_client()
        
        # We need to bypass JWT for a quick request, or we can just call the endpoint handler directly
        # Let's call the GET /api/holidays endpoint via the test client.
        # Since JWT verification is required, we can mock current_user checks or generate a valid JWT token
        # Let's look at verify_holidays.py for how JWT is generated.
        import jwt
        from datetime import datetime, timedelta
        
        # Generate token for User ID 1 (Admin/Employee doesn't matter for GET)
        token = jwt.encode(
            {"user_id": 1, "role": "Employee", "exp": datetime.utcnow() + timedelta(hours=1)},
            app.config["JWT_SECRET_KEY"],
            algorithm="HS256"
        )
        
        print("Sending GET request to /api/holidays...")
        res = client.get("/api/holidays", headers={"Authorization": f"Bearer {token}"})
        print(f"API Response Status: {res.status_code}")

    print("\n--- STEP 4: VERIFY AUTO-POPULATION IN LIVE DB ---")
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) AS count FROM holidays WHERE YEAR(date) = 2027")
            count_2027_after = cursor.fetchone()['count']
            print(f"Holidays for 2027 in live DB after API call: {count_2027_after}")
            
            cursor.execute("SELECT id, name, date FROM holidays WHERE YEAR(date) = 2027 ORDER BY date ASC LIMIT 5")
            rows = cursor.fetchall()
            print("\nFirst 5 auto-populated holidays for 2027:")
            for r in rows:
                print(f"  ID: {r['id']:<5} | Date: {str(r['date'])} | Name: {r['name']}")
    finally:
        conn.close()

if __name__ == '__main__':
    main()
