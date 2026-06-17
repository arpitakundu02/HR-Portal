import os
import sys
import json
import jwt
import datetime

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../backend')))

from app import create_app
from models import User

app = create_app()
with app.app_context():
    naitik = User.query.filter_by(employee_id='TECH-005').first()
    if not naitik:
        print("Naitik not found")
        sys.exit(1)
        
    print(f"Naitik user_id: {naitik.id}, department_id: {naitik.department_id}, role: {naitik.role}, is_line_manager: {naitik.is_line_manager}")
    
    # Generate token
    token = jwt.encode(
        {'user_id': naitik.id, 'role': naitik.role, 'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1)},
        app.config['JWT_SECRET_KEY'],
        algorithm='HS256'
    )
    
    client = app.test_client()
    
    # Case 1: No department filter (All Departments selected)
    res_all = client.get('/api/employees/directory', headers={'Authorization': f'Bearer {token}'})
    print("\n--- ALL DEPARTMENTS ---")
    print("Status:", res_all.status_code)
    data_all = res_all.get_json()
    print("Total:", data_all.get('total'))
    for emp in data_all.get('employees', []):
        print(f" - {emp['employee_id']}: {emp['name']} | Dept: {emp['department_id']} ({emp['department_name']}) | Role: {emp['role']} | LM: {emp['is_line_manager']}")

    # Case 2: Department filter = 2 (Tech)
    res_tech = client.get('/api/employees/directory?department_id=2', headers={'Authorization': f'Bearer {token}'})
    print("\n--- TECH DEPARTMENT (2) ---")
    print("Status:", res_tech.status_code)
    data_tech = res_tech.get_json()
    print("Total:", data_tech.get('total'))
    for emp in data_tech.get('employees', []):
        print(f" - {emp['employee_id']}: {emp['name']} | Dept: {emp['department_id']} ({emp['department_name']}) | Role: {emp['role']} | LM: {emp['is_line_manager']}")

    # Case 3: Department filter = 1 (Research)
    res_res = client.get('/api/employees/directory?department_id=1', headers={'Authorization': f'Bearer {token}'})
    print("\n--- RESEARCH DEPARTMENT (1) ---")
    print("Status:", res_res.status_code)
    data_res = res_res.get_json()
    print("Total:", data_res.get('total'))
    for emp in data_res.get('employees', []):
        print(f" - {emp['employee_id']}: {emp['name']} | Dept: {emp['department_id']} ({emp['department_name']}) | Role: {emp['role']} | LM: {emp['is_line_manager']}")
