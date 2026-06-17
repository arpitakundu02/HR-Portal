"""
backend/routes/exports.py
-------------------------
Admin-only HR report export endpoints for Attendance and Leave data.
Exports to Excel (.xlsx) using openpyxl.
"""

import io
from datetime import datetime
from flask import Blueprint, request, send_file, jsonify
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill
from models import Attendance, Leave, User, Department, CompOffRequest, CompOffBalance, Timesheet
from extensions import db
from utils.decorators import jwt_required

exports_bp = Blueprint("exports", __name__)

@exports_bp.route("/attendance", methods=["GET"])
@jwt_required
def export_attendance(current_user_id, current_user_role):
    """
    Export attendance records to Excel (.xlsx).
    """
    creator = User.query.get(current_user_id)
    if not creator:
        return jsonify({"error": "User not found."}), 404
        
    is_lm = getattr(creator, 'is_line_manager', False)
    
    start_date_str = request.args.get("start_date")
    end_date_str = request.args.get("end_date")
    dept_id = request.args.get("department", type=int)
    emp_id = request.args.get("employee_id", type=int)

    query = Attendance.query.join(User, Attendance.employee_id == User.id)

    if current_user_role == "Admin":
        if dept_id:
            query = query.filter(User.department_id == dept_id)
        if emp_id:
            query = query.filter(Attendance.employee_id == emp_id)
    elif is_lm:
        managed_depts = Department.query.filter_by(manager_id=current_user_id).all()
        managed_dept_ids = [d.id for d in managed_depts]
        
        # Line manager can only see reports or managed depts or themselves
        query = query.filter((User.manager_id == current_user_id) | (User.department_id.in_(managed_dept_ids)) | (User.id == current_user_id))
        
        if dept_id:
            if dept_id in managed_dept_ids or creator.department_id == dept_id:
                query = query.filter(User.department_id == dept_id)
            else:
                return jsonify({"error": "Access denied to department."}), 403
        if emp_id:
            is_permitted = User.query.filter(
                (User.id == emp_id) & 
                ((User.manager_id == current_user_id) | (User.department_id.in_(managed_dept_ids)) | (User.id == current_user_id))
            ).first() is not None
            if not is_permitted:
                return jsonify({"error": "Access denied to employee."}), 403
            query = query.filter(Attendance.employee_id == emp_id)
    else:
        # Regular employee: Only themselves
        query = query.filter(Attendance.employee_id == current_user_id)

    if start_date_str:
        try:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
            query = query.filter(Attendance.date >= start_date)
        except ValueError:
            return jsonify({"error": "start_date must be in YYYY-MM-DD format."}), 422

    if end_date_str:
        try:
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
            query = query.filter(Attendance.date <= end_date)
        except ValueError:
            return jsonify({"error": "end_date must be in YYYY-MM-DD format."}), 422

    if dept_id:
        query = query.filter(User.department_id == dept_id)

    if emp_id:
        query = query.filter(Attendance.employee_id == emp_id)

    records = query.order_by(Attendance.date.desc(), User.name.asc()).all()

    # Create Excel Workbook
    wb = Workbook()
    ws = wb.active
    ws.title = "Attendance Records"

    # Define headers
    headers = [
        "Employee Name", "Employee ID", "Department", 
        "Date", "Check-In", "Check-Out", 
        "Working Hours", "Attendance Status"
    ]
    ws.append(headers)

    # Style headers
    header_fill = PatternFill(start_color="4F46E5", end_color="4F46E5", fill_type="solid")
    header_font = Font(name="Arial", size=11, bold=True, color="FFFFFF")
    for col_num in range(1, len(headers) + 1):
        cell = ws.cell(row=1, column=col_num)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center", vertical="center")

    # Populate records
    for r in records:
        check_in_local = r.check_in.strftime("%I:%M %p") if r.check_in else "—"
        check_out_local = r.check_out.strftime("%I:%M %p") if r.check_out else "—"
        
        # Calculate status matching UI status
        status = r.get_status()

        row_data = [
            r.employee.name,
            r.employee.employee_id,
            r.employee.department.name if r.employee.department else "—",
            r.date.strftime("%Y-%m-%d"),
            check_in_local,
            check_out_local,
            float(r.working_hours) if r.working_hours else 0.0,
            status
        ]
        ws.append(row_data)

    # Align cells and auto-adjust widths
    for col in ws.columns:
        max_len = max(len(str(cell.value or '')) for cell in col)
        col_letter = col[0].column_letter
        ws.column_dimensions[col_letter].width = max(max_len + 3, 12)
        # Apply standard alignments
        for cell in col:
            if cell.row > 1:
                cell.font = Font(name="Arial", size=10)
                if col_letter in ("D", "E", "F", "G", "H"):
                    cell.alignment = Alignment(horizontal="center")
                else:
                    cell.alignment = Alignment(horizontal="left")

    # Write to in-memory binary stream
    out = io.BytesIO()
    wb.save(out)
    out.seek(0)

    filename = f"Attendance_Export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    return send_file(
        out,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=True,
        download_name=filename
    )


@exports_bp.route("/leaves", methods=["GET"])
@jwt_required
def export_leaves(current_user_id, current_user_role):
    """
    Export leave records to Excel (.xlsx).
    """
    creator = User.query.get(current_user_id)
    if not creator:
        return jsonify({"error": "User not found."}), 404
        
    is_lm = getattr(creator, 'is_line_manager', False)
    
    start_date_str = request.args.get("start_date")
    end_date_str = request.args.get("end_date")
    dept_id = request.args.get("department", type=int)
    emp_id = request.args.get("employee_id", type=int)

    query = Leave.query.join(User, Leave.employee_id == User.id)

    if current_user_role == "Admin":
        if dept_id:
            query = query.filter(User.department_id == dept_id)
        if emp_id:
            query = query.filter(Leave.employee_id == emp_id)
    elif is_lm:
        managed_depts = Department.query.filter_by(manager_id=current_user_id).all()
        managed_dept_ids = [d.id for d in managed_depts]
        
        # Line manager can only see reports or managed depts or themselves
        query = query.filter((User.manager_id == current_user_id) | (User.department_id.in_(managed_dept_ids)) | (User.id == current_user_id))
        
        if dept_id:
            if dept_id in managed_dept_ids or creator.department_id == dept_id:
                query = query.filter(User.department_id == dept_id)
            else:
                return jsonify({"error": "Access denied to department."}), 403
        if emp_id:
            is_permitted = User.query.filter(
                (User.id == emp_id) & 
                ((User.manager_id == current_user_id) | (User.department_id.in_(managed_dept_ids)) | (User.id == current_user_id))
            ).first() is not None
            if not is_permitted:
                return jsonify({"error": "Access denied to employee."}), 403
            query = query.filter(Leave.employee_id == emp_id)
    else:
        # Regular employee: Only themselves
        query = query.filter(Leave.employee_id == current_user_id)

    if start_date_str:
        try:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
            query = query.filter(Leave.start_date >= start_date)
        except ValueError:
            return jsonify({"error": "start_date must be in YYYY-MM-DD format."}), 422

    if end_date_str:
        try:
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
            query = query.filter(Leave.end_date <= end_date)
        except ValueError:
            return jsonify({"error": "end_date must be in YYYY-MM-DD format."}), 422

    if dept_id:
        query = query.filter(User.department_id == dept_id)

    if emp_id:
        query = query.filter(Leave.employee_id == emp_id)

    records = query.order_by(Leave.start_date.desc(), User.name.asc()).all()

    # Create Excel Workbook
    wb = Workbook()
    ws = wb.active
    ws.title = "Leave Records"

    # Define headers
    headers = [
        "Employee Name", "Employee ID", "Department", 
        "Leave Type", "Start Date", "End Date", 
        "Status", "Responsibility Transfer Owner"
    ]
    ws.append(headers)

    # Style headers
    header_fill = PatternFill(start_color="4F46E5", end_color="4F46E5", fill_type="solid")
    header_font = Font(name="Arial", size=11, bold=True, color="FFFFFF")
    for col_num in range(1, len(headers) + 1):
        cell = ws.cell(row=1, column=col_num)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center", vertical="center")

    # Populate records
    for r in records:
        row_data = [
            r.employee.name,
            r.employee.employee_id,
            r.employee.department.name if r.employee.department else "—",
            r.leave_type,
            r.start_date.strftime("%Y-%m-%d"),
            r.end_date.strftime("%Y-%m-%d"),
            r.status,
            r.responsibility_transfer.name if r.responsibility_transfer else "—"
        ]
        ws.append(row_data)

    # Align cells and auto-adjust widths
    for col in ws.columns:
        max_len = max(len(str(cell.value or '')) for cell in col)
        col_letter = col[0].column_letter
        ws.column_dimensions[col_letter].width = max(max_len + 3, 12)
        # Apply standard alignments
        for cell in col:
            if cell.row > 1:
                cell.font = Font(name="Arial", size=10)
                if col_letter in ("D", "E", "F", "G"):
                    cell.alignment = Alignment(horizontal="center")
                else:
                    cell.alignment = Alignment(horizontal="left")

    # Write to in-memory binary stream
    out = io.BytesIO()
    wb.save(out)
    out.seek(0)

    filename = f"Leave_Export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    return send_file(
        out,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=True,
        download_name=filename
    )


@exports_bp.route("/comp-off", methods=["GET"])
@jwt_required
def export_comp_off(current_user_id, current_user_role):
    """
    Export comp-off requests and balances report to Excel (.xlsx).
    """
    creator = User.query.get(current_user_id)
    is_lm = getattr(creator, 'is_line_manager', False) if creator else False
    if current_user_role != "Admin" and not is_lm:
        return jsonify({"error": "Admin or Line Manager access required."}), 403
    wb = Workbook()

    # Sheet 1: Comp-Off Balances
    ws1 = wb.active
    ws1.title = "Comp-Off Balances"
    headers1 = ["Employee Name", "Employee ID", "Department", "Allocated Days", "Used Days", "Remaining Balance"]
    ws1.append(headers1)

    # Style Header 1
    header_fill = PatternFill(start_color="4F46E5", end_color="4F46E5", fill_type="solid")
    header_font = Font(name="Arial", size=11, bold=True, color="FFFFFF")
    for col_num in range(1, len(headers1) + 1):
        cell = ws1.cell(row=1, column=col_num)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center", vertical="center")

    balances_query = db.session.query(CompOffBalance, User).join(User, CompOffBalance.employee_id == User.id)
    if current_user_role != "Admin":
        balances_query = balances_query.filter(User.manager_id == current_user_id)
    balances = balances_query.all()
    for cob, u in balances:
        row_data = [
            u.name,
            u.employee_id,
            u.department.name if u.department else "—",
            cob.allocated,
            cob.used,
            cob.remaining
        ]
        ws1.append(row_data)

    for col in ws1.columns:
        max_len = max(len(str(cell.value or '')) for cell in col)
        col_letter = col[0].column_letter
        ws1.column_dimensions[col_letter].width = max(max_len + 3, 12)
        for cell in col:
            if cell.row > 1:
                cell.font = Font(name="Arial", size=10)
                if col_letter in ("D", "E", "F"):
                    cell.alignment = Alignment(horizontal="center")

    # Sheet 2: Comp-Off Requests History
    ws2 = wb.create_sheet(title="Comp-Off Requests")
    headers2 = ["Employee Name", "Employee ID", "Date Worked", "Reason", "Status", "Rejection Reason", "Applied Date"]
    ws2.append(headers2)

    for col_num in range(1, len(headers2) + 1):
        cell = ws2.cell(row=1, column=col_num)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center", vertical="center")

    requests_query = CompOffRequest.query.join(User, CompOffRequest.employee_id == User.id)
    if current_user_role != "Admin":
        requests_query = requests_query.filter(User.manager_id == current_user_id)
    requests_list = requests_query.order_by(CompOffRequest.created_at.desc()).all()
    for r in requests_list:
        row_data = [
            r.employee.name,
            r.employee.employee_id,
            r.date_worked.strftime("%Y-%m-%d"),
            r.reason,
            r.status,
            r.rejection_reason or "—",
            r.created_at.strftime("%Y-%m-%d")
        ]
        ws2.append(row_data)

    for col in ws2.columns:
        max_len = max(len(str(cell.value or '')) for cell in col)
        col_letter = col[0].column_letter
        ws2.column_dimensions[col_letter].width = max(max_len + 3, 12)
        for cell in col:
            if cell.row > 1:
                cell.font = Font(name="Arial", size=10)
                if col_letter in ("C", "E", "G"):
                    cell.alignment = Alignment(horizontal="center")

    out = io.BytesIO()
    wb.save(out)
    out.seek(0)

    filename = f"CompOff_Export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    return send_file(
        out,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=True,
        download_name=filename
    )


# ------------------------------------------------------------------
# GET /api/exports/timesheets
# ------------------------------------------------------------------
@exports_bp.route("/timesheets", methods=["GET"])
@jwt_required
def export_timesheets(current_user_id, current_user_role):
    """
    Export timesheet records to Excel (.xlsx).
    """
    creator = User.query.get(current_user_id)
    if not creator:
        return jsonify({"error": "User not found."}), 404
        
    is_lm = getattr(creator, 'is_line_manager', False)
    
    start_date_str = request.args.get("start_date")
    end_date_str = request.args.get("end_date")
    dept_id = request.args.get("department", type=int)
    emp_id = request.args.get("employee_id", type=int)
    search = request.args.get("search", "").strip()

    query = Timesheet.query.join(User, Timesheet.employee_id == User.id)

    if current_user_role == "Admin":
        if dept_id:
            query = query.filter(User.department_id == dept_id)
        if emp_id:
            query = query.filter(Timesheet.employee_id == emp_id)
    elif is_lm:
        managed_depts = Department.query.filter_by(manager_id=current_user_id).all()
        managed_dept_ids = [d.id for d in managed_depts]
        
        # Line manager scope
        query = query.filter((User.manager_id == current_user_id) | (User.department_id.in_(managed_dept_ids)) | (User.id == current_user_id))
        
        if dept_id:
            if dept_id in managed_dept_ids or creator.department_id == dept_id:
                query = query.filter(User.department_id == dept_id)
            else:
                return jsonify({"error": "Access denied to department."}), 403
        if emp_id:
            is_permitted = User.query.filter(
                (User.id == emp_id) & 
                ((User.manager_id == current_user_id) | (User.department_id.in_(managed_dept_ids)) | (User.id == current_user_id))
            ).first() is not None
            if not is_permitted:
                return jsonify({"error": "Access denied to employee."}), 403
            query = query.filter(Timesheet.employee_id == emp_id)
    else:
        # Regular employee: Only themselves
        query = query.filter(Timesheet.employee_id == current_user_id)

    if start_date_str:
        try:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
            query = query.filter(Timesheet.date >= start_date)
        except ValueError:
            return jsonify({"error": "start_date must be in YYYY-MM-DD format."}), 422

    if end_date_str:
        try:
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
            query = query.filter(Timesheet.date <= end_date)
        except ValueError:
            return jsonify({"error": "end_date must be in YYYY-MM-DD format."}), 422

    if search:
        like = f"%{search}%"
        query = query.filter((Timesheet.task_name.ilike(like)) | (Timesheet.description.ilike(like)))

    records = query.order_by(Timesheet.date.desc(), User.name.asc()).all()

    # Create Excel Workbook
    wb = Workbook()
    ws = wb.active
    ws.title = "Timesheet Records"

    # Define headers
    headers = [
        "Employee Name", "Employee ID", "Department", 
        "Date", "Task Name", "Hours Spent", "Description", "Status"
    ]
    ws.append(headers)

    # Style headers
    header_fill = PatternFill(start_color="4F46E5", end_color="4F46E5", fill_type="solid")
    header_font = Font(name="Arial", size=11, bold=True, color="FFFFFF")
    for col_num in range(1, len(headers) + 1):
        cell = ws.cell(row=1, column=col_num)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center", vertical="center")

    # Populate records
    for r in records:
        row_data = [
            r.employee.name,
            r.employee.employee_id,
            r.employee.department.name if r.employee.department else "—",
            r.date.strftime("%Y-%m-%d"),
            r.task_name,
            r.hours_spent,
            r.description or "—",
            r.status
        ]
        ws.append(row_data)

    # Align cells and auto-adjust widths
    for col in ws.columns:
        max_len = max(len(str(cell.value or '')) for cell in col)
        col_letter = col[0].column_letter
        ws.column_dimensions[col_letter].width = max(max_len + 3, 12)
        for cell in col:
            if cell.row > 1:
                cell.font = Font(name="Arial", size=10)
                if col_letter in ("D", "F", "H"):
                    cell.alignment = Alignment(horizontal="center")
                else:
                    cell.alignment = Alignment(horizontal="left")

    out = io.BytesIO()
    wb.save(out)
    out.seek(0)

    filename = f"Timesheet_Export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    return send_file(
        out,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=True,
        download_name=filename
    )


# ------------------------------------------------------------------
# GET /api/exports/directory
# ------------------------------------------------------------------
@exports_bp.route("/directory", methods=["GET"])
@jwt_required
def export_directory(current_user_id, current_user_role):
    """
    Export scoped contact directory to Excel (.xlsx).
    """
    creator = User.query.get(current_user_id)
    if not creator:
        return jsonify({"error": "User not found."}), 404
        
    is_lm = getattr(creator, 'is_line_manager', False)
    
    query = User.query.filter_by(is_active=True)

    if current_user_role == "Admin":
        pass
    elif is_lm:
        # Line Managers can see:
        # 1. Admins (role == "Admin")
        # 2. Other Line Managers (is_line_manager == True)
        # 3. Direct reports, departments they manage, or themselves
        # 4. Employees in their own department
        managed_depts = Department.query.filter_by(manager_id=current_user_id).all()
        managed_dept_ids = [d.id for d in managed_depts]
        
        conds = [
            (User.role == "Admin"),
            (User.is_line_manager == True),
            (User.manager_id == current_user_id),
            (User.id == current_user_id)
        ]
        if creator.department_id is not None:
            conds.append(User.department_id == creator.department_id)
        if managed_dept_ids:
            conds.append(User.department_id.in_(managed_dept_ids))
            
        final_cond = conds[0]
        for cond in conds[1:]:
            final_cond = final_cond | cond
            
        query = query.filter(final_cond)
    else:
        if creator.department_id:
            query = query.filter_by(department_id=creator.department_id)
        else:
            query = query.filter_by(id=current_user_id)

    search = request.args.get("search", "").strip()
    department_id = request.args.get("department_id", type=int)

    if search:
        like = f"%{search}%"
        query = query.filter(
            (User.name.ilike(like)) | 
            (User.employee_id.ilike(like)) | 
            (User.email.ilike(like)) | 
            (User.phone_number.ilike(like))
        )
        
    if department_id:
        if current_user_role == "Admin" or is_lm:
            query = query.filter_by(department_id=department_id)
        else:
            if department_id == creator.department_id:
                query = query.filter_by(department_id=department_id)

    records = query.order_by(User.name).all()

    # Create Excel Workbook
    wb = Workbook()
    ws = wb.active
    ws.title = "Contact Directory"

    # Define headers
    headers = [
        "Employee ID", "Name", "Department", "Designation", "Email", "Phone Number", "Role", "Status"
    ]
    ws.append(headers)

    # Style headers
    header_fill = PatternFill(start_color="4F46E5", end_color="4F46E5", fill_type="solid")
    header_font = Font(name="Arial", size=11, bold=True, color="FFFFFF")
    for col_num in range(1, len(headers) + 1):
        cell = ws.cell(row=1, column=col_num)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center", vertical="center")

    # Dynamic status helper
    from routes.employees import _get_availability_status

    # Populate records
    for r in records:
        row_data = [
            r.employee_id,
            r.name,
            r.department.name if r.department else "—",
            r.rank or "—",
            r.email,
            r.phone_number or "—",
            "Line Manager" if r.is_line_manager else r.role,
            _get_availability_status(r)
        ]
        ws.append(row_data)

    # Align cells and auto-adjust widths
    for col in ws.columns:
        max_len = max(len(str(cell.value or '')) for cell in col)
        col_letter = col[0].column_letter
        ws.column_dimensions[col_letter].width = max(max_len + 3, 12)
        for cell in col:
            if cell.row > 1:
                cell.font = Font(name="Arial", size=10)
                if col_letter in ("A", "G", "H"):
                    cell.alignment = Alignment(horizontal="center")
                else:
                    cell.alignment = Alignment(horizontal="left")

    out = io.BytesIO()
    wb.save(out)
    out.seek(0)

    filename = f"Contact_Directory_Export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    return send_file(
        out,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=True,
        download_name=filename
    )

