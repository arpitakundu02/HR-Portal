import requests

BASE_URL = "http://localhost:5000/api"

# Admin login
admin_payload = {
    "email": "admin@hrportal.com",
    "password": "Admin@1234"
}
r = requests.post(f"{BASE_URL}/auth/login", json=admin_payload)
if r.status_code == 200:
    token = r.json().get("token")
    headers = {"Authorization": f"Bearer {token}"}
    r_approvals = requests.get(f"{BASE_URL}/approvals/pending", headers=headers)
    print("Pending Approvals returned to Admin:")
    for app in r_approvals.json():
        print(f"ID: {app['id']} | Requester: {app['requester_name']} | Approver: {app['approver_name']} (ID: {app['approver_id']}) | Module: {app['module_type']} | Target: {app['target_details']}")
else:
    print("Admin login failed:", r.text)
