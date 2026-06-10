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
from models import Attendance, Leave, User, Department
from extensions import db
from utils.decorators import admin_required

exports_bp = Blueprint("exports", __name__)

@exports_bp.route("/attendance", methods=["GET"])
@admin_required
def export_attendance(current_user_id, current_user_role):
    """
    Export attendance records to Excel (.xlsx) with admin-only restriction.
    Query params:
        start_date  (str) - YYYY-MM-DD
        end_date    (str) - YYYY-MM-DD
        department  (int) - department_id
        employee_id (int) - employee user_id
    """
    start_date_str = request.args.get("start_date")
    end_date_str = request.args.get("end_date")
    dept_id = request.args.get("department", type=int)
    emp_id = request.args.get("employee_id", type=int)

    query = Attendance.query.join(User, Attendance.employee_id == User.id)

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
        status = "Present"
        if not r.check_in:
            status = "Absent"
        elif r.check_out:
            status = "Checked Out"
        else:
            status = "Checked In"

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
@admin_required
def export_leaves(current_user_id, current_user_role):
    """
    Export leave records to Excel (.xlsx) with admin-only restriction.
    Query params:
        start_date  (str) - YYYY-MM-DD
        end_date    (str) - YYYY-MM-DD
        department  (int) - department_id
        employee_id (int) - employee user_id
    """
    start_date_str = request.args.get("start_date")
    end_date_str = request.args.get("end_date")
    dept_id = request.args.get("department", type=int)
    emp_id = request.args.get("employee_id", type=int)

    query = Leave.query.join(User, Leave.employee_id == User.id)

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
