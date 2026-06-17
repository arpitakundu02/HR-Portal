from models import User, Department

def get_dept_prefix(dept_name: str) -> str:
    if not dept_name:
        return "HR"
    name = dept_name.strip().upper()
    if name == "RESEARCH":
        return "RES"
    elif name == "TECH":
        return "TECH"
    elif name == "GIS":
        return "GIS"
    elif name == "DATA SCIENTIST":
        return "DATA"
    elif name == "BROKER":
        return "BRK"
    elif name == "EXECUTION":
        return "EXEC"
    elif name == "ACCOUNT":
        return "ACC"
    elif name == "MANAGEMENT":
        return "MGT"
    elif "HR" in name or "HUMAN RESOURCE" in name:
        return "HR"
    else:
        clean = "".join([c for c in name if c.isalnum()])
        if len(clean) >= 3:
            return clean[:4]
        return "HR"

def generate_department_employee_id(department_id) -> str:
    """Generate next sequential employee ID based on department name like TECH-001 or RES-001."""
    dept_name = None
    if department_id:
        dept = Department.query.get(department_id)
        if dept:
            dept_name = dept.name
            
    prefix = get_dept_prefix(dept_name)
    like_pattern = f"{prefix}-%"
    users = User.query.filter(User.employee_id.like(like_pattern)).all()
    
    max_num = 0
    for u in users:
        parts = u.employee_id.split("-")
        if len(parts) == 2:
            try:
                num = int(parts[1])
                if num > max_num:
                    max_num = num
            except ValueError:
                pass
                
    next_num = max_num + 1
    return f"{prefix}-{next_num:03d}"
