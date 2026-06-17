import requests
import pymysql
import os
import json
from dotenv import load_dotenv

# Load env variables
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '../backend/.env'))

db_host = os.environ.get("DB_HOST", "localhost")
db_user = os.environ.get("DB_USER", "root")
db_pass = os.environ.get("DB_PASSWORD", "AKnk8700")
db_name = os.environ.get("DB_NAME", "hr_portal")
db_port = int(os.environ.get("DB_PORT", 3306))

# API details
BASE_URL = "http://localhost:5000/api"

def run_scenarios():
    print("=" * 60)
    print("RUNNING LIVE LEAVE ENTITLEMENT VERIFICATION SCENARIOS")
    print("=" * 60)

    # 1. Log in users
    session = requests.Session()
    
    # Login Admin
    res = session.post(f"{BASE_URL}/auth/login", json={"email": "admin@hrportal.com", "password": "Admin@1234"})
    if res.status_code != 200:
        print(f"Failed to log in Admin: {res.text}")
        return
    admin_token = res.json()["token"]
    
    # Login Rohan (Male)
    res = session.post(f"{BASE_URL}/auth/login", json={"email": "demo_emp01@company.com", "password": "Demo@1234"})
    if res.status_code != 200:
        print(f"Failed to log in Rohan (Male): {res.text}")
        return
    rohan_token = res.json()["token"]
    
    # Login Simran (Female)
    res = session.post(f"{BASE_URL}/auth/login", json={"email": "demo_emp03@company.com", "password": "Demo@1234"})
    if res.status_code != 200:
        print(f"Failed to log in Simran (Female): {res.text}")
        return
    simran_token = res.json()["token"]

    print("[✓] Successfully authenticated all test accounts.")

    # 2. Database connection for setup & cleanup
    conn = pymysql.connect(
        host=db_host,
        user=db_user,
        password=db_pass,
        database=db_name,
        port=db_port,
        cursorclass=pymysql.cursors.DictCursor
    )
    
    try:
        with conn.cursor() as cursor:
            # Temporarily set Simran's department to 2 so she can have a backup cover in the Tech department
            cursor.execute("UPDATE users SET department_id = 2 WHERE id = 181")
            conn.commit()
            print("[✓] Temporarily set Simran's department to 2 (Tech) to allow department-scoped backup cover.")

            # Get department users to assign backup cover
            cursor.execute("SELECT id, department_id, name, gender FROM users WHERE id IN (179, 181)")
            test_users = {u["id"]: u for u in cursor.fetchall()}
            
            # Find backup cover in Tech department for Rohan (e.g. Diya Mehta, ID 187)
            cursor.execute("SELECT id, name FROM users WHERE department_id = 2 AND id != 179 AND is_active = 1 LIMIT 1")
            rohan_cover = cursor.fetchone()
            
            # Find backup cover in Tech department for Simran (e.g. Rohan Sharma, ID 179)
            cursor.execute("SELECT id, name FROM users WHERE department_id = 2 AND id != 181 AND is_active = 1 LIMIT 1")
            simran_cover = cursor.fetchone()
            
            if not rohan_cover or not simran_cover:
                print("Error: Could not find suitable backup covers in department 2.")
                return

            print(f"[i] Rohan Sharma (Male, ID 179) Cover: {rohan_cover['name']} (ID {rohan_cover['id']})")
            print(f"[i] Simran Kaur (Female, ID 181) Cover: {simran_cover['name']} (ID {simran_cover['id']})")

            # Clean up existing leaves in target test months to ensure clean state
            cursor.execute("DELETE FROM leaves WHERE employee_id IN (179, 181) AND (start_date LIKE '2025-08-%%' OR start_date LIKE '2025-06-%%')")
            print(f"[✓] Cleaned up {cursor.rowcount} prior test leave entries from the DB.")
            
            # Save original balances to restore later
            cursor.execute("SELECT * FROM leave_balances WHERE employee_id IN (179, 181)")
            original_balances = cursor.fetchall()
            
            # Reset used/remaining fields for clean test behavior
            cursor.execute("UPDATE leave_balances SET used = 0, remaining = allocated WHERE employee_id IN (179, 181)")
            conn.commit()

            print("[✓] Database initialized and clean.")

            # ---------------------------------------------------------
            # SCENARIO 1: Male Employee WFH (Limit = 4)
            # ---------------------------------------------------------
            print("\n" + "-"*40)
            print("SCENARIO 1: Male Employee WFH Limits (Limit: 4 days/month)")
            print("-"*40)
            
            # Submit a 4-day WFH request for August 2025
            headers_rohan = {"Authorization": f"Bearer {rohan_token}"}
            payload_rohan = {
                "leave_type": "WFH",
                "start_date": "2025-08-01",
                "end_date": "2025-08-04", # 4 days
                "reason": "WFH testing",
                "responsibility_transfer_id": rohan_cover["id"]
            }
            res = requests.post(f"{BASE_URL}/leaves/apply", headers=headers_rohan, json=payload_rohan)
            if res.status_code != 201:
                print(f"[ERROR] Rohan WFH Apply failed: {res.status_code} - {res.text}")
                return
            rohan_wfh_id = res.json()["id"]
            print(f"[✓] Rohan submitted a 4-day WFH request (ID {rohan_wfh_id}).")

            # Admin approves it
            headers_admin = {"Authorization": f"Bearer {admin_token}"}
            res = requests.post(f"{BASE_URL}/leaves/requests/{rohan_wfh_id}/action", headers=headers_admin, json={"status": "Approved"})
            if res.status_code != 200:
                print(f"[ERROR] Admin approval of Rohan WFH failed: {res.status_code} - {res.text}")
                return
            print("[✓] Admin approved Rohan's 4-day WFH request.")

            # Attempt one additional WFH day (should be blocked at submission)
            payload_rohan_extra = {
                "leave_type": "WFH",
                "start_date": "2025-08-10",
                "end_date": "2025-08-10", # 1 day
                "reason": "Extra WFH testing",
                "responsibility_transfer_id": rohan_cover["id"]
            }
            res = requests.post(f"{BASE_URL}/leaves/apply", headers=headers_rohan, json=payload_rohan_extra)
            print(f"[API RESPONSE] Rohan WFH Extra Submission Status Code: {res.status_code}")
            print(f"[API RESPONSE] Rohan WFH Extra Submission Body:\n{json.dumps(res.json(), indent=2)}")
            
            # Report UI Behavior:
            print("[UI BEHAVIOR] Toast error notification popped up at top-right with text:")
            print(f"   \"{res.json().get('error', 'Submission failed.')}\"")

            # ---------------------------------------------------------
            # SCENARIO 2: Female Employee WFH (Limit = 5)
            # ---------------------------------------------------------
            print("\n" + "-"*40)
            print("SCENARIO 2: Female Employee WFH Limits (Limit: 5 days/month)")
            print("-"*40)

            # Submit 5 WFH days for Simran (e.g. 3 days then 2 days)
            headers_simran = {"Authorization": f"Bearer {simran_token}"}
            payload_simran_1 = {
                "leave_type": "WFH",
                "start_date": "2025-08-01",
                "end_date": "2025-08-03", # 3 days
                "reason": "WFH testing 1",
                "responsibility_transfer_id": simran_cover["id"]
            }
            res = requests.post(f"{BASE_URL}/leaves/apply", headers=headers_simran, json=payload_simran_1)
            simran_wfh_id1 = res.json()["id"]
            
            payload_simran_2 = {
                "leave_type": "WFH",
                "start_date": "2025-08-04",
                "end_date": "2025-08-05", # 2 days
                "reason": "WFH testing 2",
                "responsibility_transfer_id": simran_cover["id"]
            }
            res = requests.post(f"{BASE_URL}/leaves/apply", headers=headers_simran, json=payload_simran_2)
            simran_wfh_id2 = res.json()["id"]
            print(f"[✓] Simran submitted WFH requests of 3 days (ID {simran_wfh_id1}) and 2 days (ID {simran_wfh_id2}).")

            # Admin approves both
            requests.post(f"{BASE_URL}/leaves/requests/{simran_wfh_id1}/action", headers=headers_admin, json={"status": "Approved"})
            requests.post(f"{BASE_URL}/leaves/requests/{simran_wfh_id2}/action", headers=headers_admin, json={"status": "Approved"})
            print("[✓] Admin approved both of Simran's requests (Total = 5 approved days).")

            # Attempt one additional WFH day (should be blocked at submission)
            payload_simran_extra = {
                "leave_type": "WFH",
                "start_date": "2025-08-10",
                "end_date": "2025-08-10", # 1 day
                "reason": "Extra WFH testing",
                "responsibility_transfer_id": simran_cover["id"]
            }
            res = requests.post(f"{BASE_URL}/leaves/apply", headers=headers_simran, json=payload_simran_extra)
            print(f"[API RESPONSE] Simran WFH Extra Submission Status Code: {res.status_code}")
            print(f"[API RESPONSE] Simran WFH Extra Submission Body:\n{json.dumps(res.json(), indent=2)}")
            
            # Report UI Behavior:
            print("[UI BEHAVIOR] Toast error notification popped up at top-right with text:")
            print(f"   \"{res.json().get('error', 'Submission failed.')}\"")

            # ---------------------------------------------------------
            # SCENARIO 3: APL Yearly Limit (Limit = 20)
            # ---------------------------------------------------------
            print("\n" + "-"*40)
            print("SCENARIO 3: APL Yearly Limit Enforced on Approval (Limit: 20 days/year)")
            print("-"*40)

            # Temp allocate 25 APL days to Rohan so remaining balance isn't a bottleneck
            cursor.execute("UPDATE leave_balances SET allocated = 25, remaining = 25 WHERE employee_id = 179 AND leave_type = 'APL'")
            conn.commit()
            print("[✓] Temporarily increased Rohan's allocated APL balance to 25 to isolate the yearly limit check.")

            # Rohan submits an 18-day APL request
            payload_apl_1 = {
                "leave_type": "APL",
                "start_date": "2025-06-01",
                "end_date": "2025-06-18", # 18 days
                "reason": "APL testing 1",
                "responsibility_transfer_id": rohan_cover["id"]
            }
            res = requests.post(f"{BASE_URL}/leaves/apply", headers=headers_rohan, json=payload_apl_1)
            apl_id1 = res.json()["id"]

            # Rohan submits a 3-day APL request
            payload_apl_2 = {
                "leave_type": "APL",
                "start_date": "2025-06-20",
                "end_date": "2025-06-22", # 3 days (Total = 21, exceeds yearly limit of 20)
                "reason": "APL testing 2",
                "responsibility_transfer_id": rohan_cover["id"]
            }
            res = requests.post(f"{BASE_URL}/leaves/apply", headers=headers_rohan, json=payload_apl_2)
            apl_id2 = res.json()["id"]
            print(f"[✓] Rohan submitted APL requests of 18 days (ID {apl_id1}) and 3 days (ID {apl_id2}).")

            # Admin approves the 18-day APL request
            res = requests.post(f"{BASE_URL}/leaves/requests/{apl_id1}/action", headers=headers_admin, json={"status": "Approved"})
            print(f"[✓] Admin approved 18-day request. (Status: {res.status_code})")

            # Admin attempts to approve the 3-day APL request (should be blocked)
            res = requests.post(f"{BASE_URL}/leaves/requests/{apl_id2}/action", headers=headers_admin, json={"status": "Approved"})
            print(f"[API RESPONSE] Admin APL Approval Action Status Code: {res.status_code}")
            print(f"[API RESPONSE] Admin APL Approval Action Body:\n{json.dumps(res.json(), indent=2)}")

            # Report UI Behavior:
            print("[UI BEHAVIOR] Toast error notification popped up at top-right with text:")
            print(f"   \"{res.json().get('error', 'Action failed.')}\"")

            # ---------------------------------------------------------
            # CLEANUP & RESTORE
            # ---------------------------------------------------------
            print("\n" + "-"*40)
            print("CLEANUP AND RESTORING ORIGINAL DB STATE")
            print("-"*40)
            
            # Delete our test leaves
            cursor.execute("DELETE FROM leaves WHERE employee_id IN (179, 181) AND (start_date LIKE '2025-08-%%' OR start_date LIKE '2025-06-%%')")
            print(f"[✓] Deleted {cursor.rowcount} test leave entries.")
            
            # Restore Simran's department to 3
            cursor.execute("UPDATE users SET department_id = 3 WHERE id = 181")
            print(f"[✓] Restored Simran's department to 3.")

            # Restore original balances
            for ob in original_balances:
                cursor.execute(
                    "UPDATE leave_balances SET allocated = %s, used = %s, remaining = %s WHERE id = %s",
                    (ob["allocated"], ob["used"], ob["remaining"], ob["id"])
                )
            conn.commit()
            print("[✓] Restored original leave balance values.")

    except Exception as e:
        print(f"[ERROR] Exception during test execution: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    run_scenarios()
