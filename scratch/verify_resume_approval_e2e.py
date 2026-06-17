import requests
import os
import pymysql
from dotenv import load_dotenv

# Load environment
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

def test_resume_approval_workflow():
    print("============================================================")
    print("STARTING RESUME APPROVAL WORKFLOW END-TO-END VERIFICATION")
    print("============================================================")
    
    # 1. Login as Aarav Patel (ID 180, Manager is Ananya Sen ID 186)
    print("\n[1] Logging in as Aarav Patel (Employee)...")
    login_payload = {
        "email": "demo_emp02@company.com",
        "password": "Demo@1234"
    }
    r = requests.post(f"{BASE_URL}/auth/login", json=login_payload)
    if r.status_code != 200:
        print(f"Failed to log in as employee: {r.text}")
        return
    emp_token = r.json().get("token")
    emp_headers = {"Authorization": f"Bearer {emp_token}"}
    print("[✓] Logged in successfully.")

    # 2. Upload a dummy resume
    print("\n[2] Uploading resume as Aarav Patel...")
    dummy_file_content = b"%PDF-1.4 dummy pdf content"
    files = {
        "resume": ("aarav_patel_resume.pdf", dummy_file_content, "application/pdf")
    }
    # Clear any previous resume update requests from DB to make logs clean
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM approval_requests WHERE module_type='ResumeUpdate' AND requester_id=180")
            cursor.execute("DELETE FROM resume_update_requests WHERE employee_id=180")
            # Set employee resume url to NULL to begin test
            cursor.execute("UPDATE users SET resume_url=NULL WHERE id=180")
        conn.commit()
    finally:
        conn.close()

    r = requests.post(f"{BASE_URL}/employees/180/resume", headers=emp_headers, files=files)
    print(f"Response: {r.status_code} - {r.text}")
    if r.status_code != 200:
        print("Failed to upload resume.")
        return
    print("[✓] Resume uploaded successfully.")

    # 3. Verify ResumeUpdate request is created in database
    print("\n[3] Checking database records...")
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM resume_update_requests WHERE employee_id=180 ORDER BY created_at DESC LIMIT 1")
            db_request = cursor.fetchone()
            if not db_request:
                print("[-] No ResumeUpdateRequest found in database.")
                return
            print(f"[✓] ResumeUpdateRequest Record in DB: {db_request}")
            
            cursor.execute("SELECT * FROM approval_requests WHERE target_id=%s AND module_type='ResumeUpdate'", (db_request["id"],))
            approval_request = cursor.fetchone()
            if not approval_request:
                print("[-] No ApprovalRequest found in database.")
                return
            print(f"[✓] ApprovalRequest Record in DB: {approval_request}")
            
            approval_req_id = approval_request["id"]
            approver_id = approval_request["approver_id"]
            target_id = db_request["id"]
            resume_url = db_request["resume_url"]
    finally:
        conn.close()

    # 4. Login as Admin
    print("\n[4] Logging in as Admin...")
    admin_payload = {
        "email": "admin@hrportal.com",
        "password": "Admin@1234"
    }
    r = requests.post(f"{BASE_URL}/auth/login", json=admin_payload)
    if r.status_code != 200:
        print(f"Failed to log in as Admin: {r.text}")
        return
    admin_token = r.json().get("token")
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    print("[✓] Logged in successfully.")

    # 5. Verify it appears in Admin Approvals page
    print("\n[5] Verifying request visibility in Admin Approvals page...")
    r = requests.get(f"{BASE_URL}/approvals/pending", headers=admin_headers)
    print(f"Pending approvals: {r.status_code}")
    pending_list = r.json()
    found_in_admin = False
    for req in pending_list:
        if req["module_type"] == "ResumeUpdate" and req["id"] == approval_req_id:
            found_in_admin = True
            print(f"[✓] Admin can see request! Details: {req}")
            break
            
    if not found_in_admin:
        print("[-] FAILED: Admin cannot see the ResumeUpdate request in pending approvals.")
        return

    # 6. Admin approves the request
    print("\n[6] Admin approving the request...")
    approve_payload = {
        "status": "Approved",
        "comments": "Looks good, approved."
    }
    r = requests.post(f"{BASE_URL}/approvals/{approval_req_id}/action", headers=admin_headers, json=approve_payload)
    print(f"Action response: {r.status_code} - {r.text}")
    if r.status_code != 200:
        print("[-] FAILED: Admin failed to action (approve) the request.")
        return

    # 7. Verify approved resume becomes visible on profile
    print("\n[7] Verifying approved resume URL on user profile...")
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT resume_url FROM users WHERE id=180")
            profile = cursor.fetchone()
            print(f"Profile resume_url in DB: {profile['resume_url']}")
            if profile["resume_url"] == resume_url:
                print("[✓] PASSED: Approved resume url is set on user profile.")
            else:
                print("[-] FAILED: resume_url was not updated on user profile.")
    finally:
        conn.close()

    # 8. Upload another resume as Aarav Patel for Rejection testing
    print("\n[8] Uploading new resume for rejection test...")
    files_2 = {
        "resume": ("aarav_patel_new_resume.pdf", b"%PDF-1.4 new dummy pdf content", "application/pdf")
    }
    r = requests.post(f"{BASE_URL}/employees/180/resume", headers=emp_headers, files=files_2)
    if r.status_code != 200:
        print("[-] Failed to upload second resume.")
        return

    # Get new approval request details
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id FROM resume_update_requests WHERE employee_id=180 AND status='Pending' ORDER BY created_at DESC LIMIT 1")
            new_db_req = cursor.fetchone()
            cursor.execute("SELECT id FROM approval_requests WHERE target_id=%s AND module_type='ResumeUpdate' AND status='Pending'", (new_db_req["id"],))
            new_approval_req = cursor.fetchone()
            new_approval_req_id = new_approval_req["id"]
    finally:
        conn.close()

    # 9. Admin rejects the second request
    print("\n[9] Admin rejecting the second request...")
    reject_payload = {
        "status": "Rejected",
        "comments": "Invalid format or incomplete details."
    }
    r = requests.post(f"{BASE_URL}/approvals/{new_approval_req_id}/action", headers=admin_headers, json=reject_payload)
    print(f"Action response: {r.status_code} - {r.text}")
    if r.status_code != 200:
        print("[-] FAILED: Admin failed to action (reject) the request.")
        return

    # 10. Verify rejected resume does not replace the existing approved resume
    print("\n[10] Verifying profile resume url remains the previously approved one...")
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT resume_url FROM users WHERE id=180")
            profile = cursor.fetchone()
            print(f"Profile resume_url in DB: {profile['resume_url']}")
            if profile["resume_url"] == resume_url:
                print("[✓] PASSED: Profile resume URL remains the previously approved one.")
            else:
                print("[-] FAILED: Profile resume URL was overwritten by the rejected one.")
    finally:
        conn.close()

    print("\n============================================================")
    print("VERIFICATION COMPLETED SUCCESSFULLY")
    print("============================================================")

if __name__ == "__main__":
    test_resume_approval_workflow()
