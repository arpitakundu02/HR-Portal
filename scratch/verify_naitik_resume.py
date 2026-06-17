import requests
import os
import pymysql
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '../backend/.env'))

db_host = os.environ.get("DB_HOST", "localhost")
db_user = os.environ.get("DB_USER", "root")
db_pass = os.environ.get("DB_PASSWORD", "AKnk8700")
db_name = os.environ.get("DB_NAME", "hr_portal")
db_port = int(os.environ.get("DB_PORT", 3306))

BASE_URL = "http://localhost:5000/api"

def get_db_connection():
    return pymysql.connect(
        host=db_host,
        user=db_user,
        password=db_pass,
        database=db_name,
        port=db_port,
        cursorclass=pymysql.cursors.DictCursor
    )

def main():
    print("=== Verification Test for Naitik's Resume Upload ===")
    
    # 1. Login as Naitik (ID 494)
    print("\n[1] Logging in as Naitik...")
    login_payload = {
        "email": "arpitakundu0211@gmail.com",
        "password": "Demo@1234"
    }
    r = requests.post(f"{BASE_URL}/auth/login", json=login_payload)
    if r.status_code != 200:
        print(f"Naitik login failed: {r.text}")
        return
    token = r.json().get("token")
    headers = {"Authorization": f"Bearer {token}"}
    print("[✓] Naitik logged in successfully.")

    # Clean up any previous pending approvals for Naitik to avoid confusion
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM approval_requests WHERE requester_id=494")
            cursor.execute("DELETE FROM resume_update_requests WHERE employee_id=494")
            cursor.execute("UPDATE users SET resume_url=NULL WHERE id=494")
        conn.commit()
    finally:
        conn.close()

    # 2. Submit new resume upload request
    print("\n[2] Submitting resume upload request...")
    files = {
        "resume": ("naitik_test_resume.pdf", b"%PDF-1.4 test resume pdf content", "application/pdf")
    }
    r = requests.post(f"{BASE_URL}/employees/494/resume", headers=headers, files=files)
    print(f"Upload API response: {r.status_code} - {r.text}")
    if r.status_code != 200:
        print("Upload failed.")
        return
        
    # 3. Check database records
    print("\n[3] Checking database records...")
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM resume_update_requests WHERE employee_id=494 ORDER BY id DESC LIMIT 1")
            db_req = cursor.fetchone()
            print("Created ResumeUpdateRequest record:")
            print(db_req)
            
            cursor.execute("SELECT * FROM approval_requests WHERE requester_id=494 ORDER BY id DESC LIMIT 1")
            db_app = cursor.fetchone()
            print("\nCreated ApprovalRequest record:")
            print(db_app)
            
            app_id = db_app["id"]
            target_resume_url = db_req["resume_url"]
    finally:
        conn.close()

    # 4. Login as Admin
    print("\n[4] Logging in as Admin...")
    admin_payload = {
        "email": "admin@hrportal.com",
        "password": "Admin@1234"
    }
    r = requests.post(f"{BASE_URL}/auth/login", json=admin_payload)
    admin_token = r.json().get("token")
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    print("[✓] Admin logged in successfully.")

    # 5. Get pending approvals as Admin
    print("\n[5] Getting pending approvals for Admin...")
    r = requests.get(f"{BASE_URL}/approvals/pending", headers=admin_headers)
    print(f"API status code: {r.status_code}")
    pending = r.json()
    found = False
    for req in pending:
        if req["id"] == app_id:
            found = True
            print("Found request in Admin's approvals list:")
            print(req)
            break
    if not found:
        print("[-] FAILED: Request not found in Admin's approvals.")
        return

    # 6. Admin approves the request
    print("\n[6] Admin approving request...")
    r = requests.post(f"{BASE_URL}/approvals/{app_id}/action", headers=admin_headers, json={
        "status": "Approved",
        "comments": "Approved by Admin"
    })
    print(f"Approve API response: {r.status_code} - {r.text}")

    # 7. Verify user profile resume URL
    print("\n[7] Verifying user profile resume URL is updated...")
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT resume_url FROM users WHERE id=494")
            user_rec = cursor.fetchone()
            print(f"Active resume URL on profile: {user_rec['resume_url']}")
            if user_rec["resume_url"] == target_resume_url:
                print("[✓] PASSED: Resume approval is fully verified and working!")
            else:
                print("[-] FAILED: Profile resume URL not updated.")
    finally:
        conn.close()

if __name__ == "__main__":
    main()
