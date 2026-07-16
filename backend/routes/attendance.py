"""
backend/routes/attendance.py
-----------------------------
Attendance management with geolocation-based check-in validation.

Endpoints:
  GET  /api/attendance/status   - Today's check-in/out status for current employee
  POST /api/attendance/checkin  - Check in (validates office geolocation radius)
  POST /api/attendance/checkout - Check out (auto-calculates working hours)
  GET  /api/attendance/history  - Attendance history (Employee: own; Admin: all or by emp)
"""

from datetime import datetime, date
from flask import Blueprint, request, jsonify, current_app
from models import Attendance, User, SystemSetting, AttendanceAdjustment
from extensions import db
from utils.decorators import jwt_required, admin_required
from utils.geo import is_within_office_radius

attendance_bp = Blueprint("attendance", __name__)


def _get_company_date():
    """Return the current date in Asia/Kolkata (IST) timezone."""
    import datetime as dt
    kolkata_tz = dt.timezone(dt.timedelta(hours=5, minutes=30))
    return dt.datetime.now(kolkata_tz).date()



# ------------------------------------------------------------------
# GET /api/attendance/status
# ------------------------------------------------------------------
@attendance_bp.route("/status", methods=["GET"])
@jwt_required
def today_status(current_user_id, current_user_role):
    """Return the current employee's attendance record for today."""
    today = _get_company_date()
    record = Attendance.query.filter_by(employee_id=current_user_id, date=today).first()
    if not record:
        import datetime as dt
        yesterday = today - dt.timedelta(days=1)
        prev_record = Attendance.query.filter_by(employee_id=current_user_id, date=yesterday).first()
        if prev_record and not prev_record.check_out:
            record = prev_record

    if not record:
        return jsonify({
            "status": "not_checked_in",
            "check_in": None,
            "check_out": None,
            "working_hours": 0.0,
        }), 200

    status = "checked_out" if record.check_out else "checked_in"
    return jsonify({
        "status": status,
        **record.to_dict(),
    }), 200


# ------------------------------------------------------------------
# POST /api/attendance/checkin
# ------------------------------------------------------------------
@attendance_bp.route("/checkin", methods=["POST"])
@jwt_required
def check_in(current_user_id, current_user_role):
    """
    Record check-in for the authenticated employee.
    Validates that the employee is within the configured office radius.

    Request body:
        {
            "latitude": 28.6139,
            "longitude": 77.2090
        }
    """
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body must be JSON."}), 400

    lat = data.get("latitude")
    lon = data.get("longitude")

    if lat is None or lon is None:
        return jsonify({"error": "latitude and longitude are required."}), 422

    try:
        lat = float(lat)
        lon = float(lon)
    except (TypeError, ValueError):
        return jsonify({"error": "latitude and longitude must be numeric."}), 422

    # Geolocation radius validation from database settings (fall back to env config)
    db_lat = SystemSetting.query.filter_by(key="office_latitude").first()
    db_lon = SystemSetting.query.filter_by(key="office_longitude").first()
    db_rad = SystemSetting.query.filter_by(key="office_radius_meters").first()

    office_lat = float(db_lat.value) if db_lat else current_app.config["OFFICE_LATITUDE"]
    office_lon = float(db_lon.value) if db_lon else current_app.config["OFFICE_LONGITUDE"]
    radius = float(db_rad.value) if db_rad else current_app.config["OFFICE_RADIUS_METERS"]

    if not is_within_office_radius(lat, lon, office_lat, office_lon, radius):
        from utils.geo import haversine_distance
        dist = haversine_distance(lat, lon, office_lat, office_lon)
        print(f"[DEBUG] User location: {lat}, {lon}")
        print(f"[DEBUG] Office location: {office_lat}, {office_lon}")
        print(f"[DEBUG] Calculated distance: {dist} meters")
        return jsonify({
            "error": f"You must be within {radius} metres of the office to check in.",
            "allowed": False,
            "debug_info": {
                "user_latitude": lat,
                "user_longitude": lon,
                "office_latitude": office_lat,
                "office_longitude": office_lon,
                "distance_meters": dist
            }
        }), 403

    today = _get_company_date()
    existing = Attendance.query.filter_by(employee_id=current_user_id, date=today).first()

    # Block check-in if there is an active unchecked-out shift from yesterday
    import datetime as dt
    yesterday = today - dt.timedelta(days=1)
    prev_record = Attendance.query.filter_by(employee_id=current_user_id, date=yesterday).first()
    if prev_record and not prev_record.check_out:
        return jsonify({"error": "You have an active checked-in shift from yesterday. Please check out first."}), 409

    if existing and existing.check_in:
        return jsonify({"error": "Already checked in for today."}), 409

    if existing:
        existing.check_in = datetime.utcnow()
        existing.latitude = lat
        existing.longitude = lon
        record = existing
    else:
        record = Attendance(
            employee_id=current_user_id,
            date=today,
            check_in=datetime.utcnow(),
            latitude=lat,
            longitude=lon,
        )
        db.session.add(record)

    db.session.commit()
    return jsonify({"message": "Check-in recorded successfully.", **record.to_dict()}), 201


# ------------------------------------------------------------------
# POST /api/attendance/checkout
# ------------------------------------------------------------------
@attendance_bp.route("/checkout", methods=["POST"])
@jwt_required
def check_out(current_user_id, current_user_role):
    """
    Record check-out for the authenticated employee.
    Automatically calculates total working hours.
    No geolocation required for check-out.
    """
    today = _get_company_date()
    record = Attendance.query.filter_by(employee_id=current_user_id, date=today).first()
    if not record:
        import datetime as dt
        yesterday = today - dt.timedelta(days=1)
        record = Attendance.query.filter_by(employee_id=current_user_id, date=yesterday).first()

    if not record or not record.check_in:
        return jsonify({"error": "No check-in found for today. Please check in first."}), 400

    if record.check_out:
        return jsonify({"error": "Already checked out for today."}), 409

    record.check_out = datetime.utcnow()
    record.calculate_hours()
    db.session.commit()

    return jsonify({
        "message": f"Check-out recorded. Working hours: {float(record.working_hours):.2f}h",
        **record.to_dict(),
    }), 200


# ------------------------------------------------------------------
# GET /api/attendance/history
# ------------------------------------------------------------------
@attendance_bp.route("/history", methods=["GET"])
@jwt_required
def history(current_user_id, current_user_role):
    """
    Fetch attendance history.
    - Employee: Own records only.
    - Admin: All records or filtered by ?employee_id=, ?month=YYYY-MM

    Query params:
        employee_id (int)    - Admin only: filter by employee
        month       (str)    - Format YYYY-MM, filter records in that month
        page        (int)    - Page number (default 1)
        per_page    (int)    - Results per page (default 30)
    """
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 30, type=int)

    if current_user_role == "Admin":
        query = Attendance.query
        if emp_id := request.args.get("employee_id", type=int):
            query = query.filter_by(employee_id=emp_id)
    else:
        query = Attendance.query.filter_by(employee_id=current_user_id)

    # Optional month filter
    if month_str := request.args.get("month"):
        try:
            year, month = map(int, month_str.split("-"))
            query = query.filter(
                db.extract("year", Attendance.date) == year,
                db.extract("month", Attendance.date) == month,
            )
        except (ValueError, AttributeError):
            return jsonify({"error": "month must be in YYYY-MM format."}), 422

    pagination = query.order_by(Attendance.date.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return jsonify({
        "records": [r.to_dict() for r in pagination.items],
        "total": pagination.total,
        "page": page,
        "pages": pagination.pages,
    }), 200


# ------------------------------------------------------------------
# GET /api/attendance/settings  (JWT authenticated)
# ------------------------------------------------------------------
@attendance_bp.route("/settings", methods=["GET"])
@jwt_required
def get_settings(current_user_id, current_user_role):
    """Retrieve currently stored office settings from database, with fallback to config."""
    db_lat = SystemSetting.query.filter_by(key="office_latitude").first()
    db_lon = SystemSetting.query.filter_by(key="office_longitude").first()
    db_rad = SystemSetting.query.filter_by(key="office_radius_meters").first()
    db_by  = SystemSetting.query.filter_by(key="office_updated_by_name").first()
    db_at  = SystemSetting.query.filter_by(key="office_updated_at").first()

    lat = float(db_lat.value) if db_lat else current_app.config["OFFICE_LATITUDE"]
    lon = float(db_lon.value) if db_lon else current_app.config["OFFICE_LONGITUDE"]
    radius = float(db_rad.value) if db_rad else current_app.config["OFFICE_RADIUS_METERS"]
    updated_by = db_by.value if db_by else "System Config"
    updated_at = db_at.value if db_at else datetime.utcnow().isoformat()

    return jsonify({
        "latitude": lat,
        "longitude": lon,
        "radius_meters": radius,
        "updated_by": updated_by,
        "updated_at": updated_at
    }), 200


# ------------------------------------------------------------------
# POST /api/attendance/settings  (Admin only)
# ------------------------------------------------------------------
@attendance_bp.route("/settings", methods=["POST"])
@admin_required
def update_settings(current_user_id, current_user_role):
    """Update office geofencing coordinates in database."""
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body must be JSON."}), 400

    lat = data.get("latitude")
    lon = data.get("longitude")
    radius = data.get("radius_meters")

    if lat is None or lon is None or radius is None:
        return jsonify({"error": "latitude, longitude, and radius_meters are required."}), 422

    try:
        lat = float(lat)
        lon = float(lon)
        radius = float(radius)
    except (TypeError, ValueError):
        return jsonify({"error": "latitude, longitude, and radius_meters must be numeric."}), 422

    # Validation
    if not (-90 <= lat <= 90):
        return jsonify({"error": "Latitude must be between -90 and 90 degrees."}), 422
    if not (-180 <= lon <= 180):
        return jsonify({"error": "Longitude must be between -180 and 180 degrees."}), 422
    if radius <= 0:
        return jsonify({"error": "Radius must be greater than 0 meters."}), 422

    admin = User.query.get(current_user_id)
    admin_name = admin.name if admin else "Admin"

    settings_to_update = {
        "office_latitude": str(lat),
        "office_longitude": str(lon),
        "office_radius_meters": str(radius),
        "office_updated_by_name": admin_name,
        "office_updated_at": datetime.utcnow().isoformat()
    }

    for key, val in settings_to_update.items():
        record = SystemSetting.query.filter_by(key=key).first()
        if record:
            record.value = val
        else:
            record = SystemSetting(key=key, value=val)
            db.session.add(record)

    db.session.commit()
    return jsonify({
        "message": "Office settings updated successfully.",
        "latitude": lat,
        "longitude": lon,
        "radius_meters": radius,
        "updated_by": admin_name,
        "updated_at": settings_to_update["office_updated_at"]
    }), 200

# ------------------------------------------------------------------
# GET /api/attendance/stats
# ------------------------------------------------------------------
@attendance_bp.route("/stats", methods=["GET"])
@admin_required
def get_attendance_stats(current_user_id, current_user_role):
    """
    Get aggregated attendance statistics for today.
    Returns present and absent count for active employees (or all employees if include_inactive=true).
    """
    from sqlalchemy import func
    
    today = _get_company_date()
    include_inactive = request.args.get("include_inactive", "false").lower() == "true"
    
    # Base user query for total head count
    user_query = User.query
    if not include_inactive:
        user_query = user_query.filter_by(is_active=True)
    total_users_count = user_query.count()
    
    # Query present employees today
    present_query = Attendance.query.join(
        User, Attendance.employee_id == User.id
    ).filter(
        Attendance.date == today,
        Attendance.check_in != None
    )
    
    if not include_inactive:
        present_query = present_query.filter(User.is_active == True)
        
    present_today = 0
    for r in present_query.all():
        if r.get_status() in ("Present", "Half Day"):
            present_today += 1
            
    absent_today = max(0, total_users_count - present_today)
    
    return jsonify({
        "present_today": present_today,
        "absent_today": absent_today
    }), 200


# ------------------------------------------------------------------
# POST /api/attendance/test_email_config
# ------------------------------------------------------------------
@attendance_bp.route("/test_email_config", methods=["POST"])
@admin_required
def test_email_config(current_user_id, current_user_role):
    """
    Validate SMTP parameters directly by attempting to send a test email.
    """
    data = request.get_json(silent=True) or {}
    host = data.get("smtp_host", "smtp.gmail.com")
    port = data.get("smtp_port", 587)
    user = data.get("smtp_user")
    password = data.get("smtp_password")
    recipient = data.get("recipient")

    if not user or not password or not recipient:
        return jsonify({"error": "smtp_user, smtp_password, and recipient are required."}), 422

    try:
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart

        msg = MIMEMultipart("alternative")
        msg["Subject"] = "HR Portal - SMTP Configuration Test"
        msg["From"] = user
        msg["To"] = recipient
        body = "<h3>SMTP Configuration Test Successful</h3><p>Your SMTP credentials are correct!</p>"
        msg.attach(MIMEText(body, "html"))

        with smtplib.SMTP(host, int(port), timeout=10) as server:
            server.ehlo()
            server.starttls()
            server.login(user, password)
            server.sendmail(user, recipient, msg.as_string())

        return jsonify({"success": True, "message": f"Test email sent successfully to {recipient}!"}), 200
    except Exception as exc:
        return jsonify({"success": False, "error": str(exc)}), 500


# Helper to parse ISO / standard datetime strings robustly
def _parse_regularization_datetime(dt_str):
    if not dt_str:
        return None
    if dt_str.endswith("Z"):
        dt_str = dt_str[:-1]
    dt_str = dt_str.replace("T", " ")
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d %H:%M:%S.%f"):
        try:
            return datetime.strptime(dt_str, fmt)
        except ValueError:
            pass
    try:
        return datetime.fromisoformat(dt_str)
    except ValueError:
        raise ValueError(f"Invalid datetime format: {dt_str}")


# ------------------------------------------------------------------
# POST /api/attendance/regularization
# ------------------------------------------------------------------
@attendance_bp.route("/regularization", methods=["POST"])
@jwt_required
def create_regularization(current_user_id, current_user_role):
    """
    Submit a new attendance regularization request.
    Validations:
      - No future dates.
      - Within last 30 days.
      - No duplicate Pending requests for same date.
      - Reason length >= 10 characters.
      - Monthly limit of 4 requests (all statuses: Pending, Approved, Rejected).
    """
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body must be JSON."}), 400

    date_str = data.get("date")
    check_in_str = data.get("check_in")
    check_out_str = data.get("check_out")
    reason = data.get("reason", "").strip()

    if not date_str:
        return jsonify({"error": "Date is required."}), 422
    if not reason:
        return jsonify({"error": "Reason is required."}), 422
    if len(reason) < 10:
        return jsonify({"error": "Reason must be at least 10 characters."}), 422

    try:
        req_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        return jsonify({"error": "Invalid date format. Use YYYY-MM-DD."}), 422

    # Check future date
    if req_date > _get_company_date():
        return jsonify({"error": "Regularization requests for future dates are rejected."}), 422

    # Check older than 30 days
    days_ago = (_get_company_date() - req_date).days
    if days_ago > 30:
        return jsonify({"error": "Regularization requests are restricted to dates within the last 30 days."}), 422

    # Check duplicates for same date
    duplicate = AttendanceAdjustment.query.filter_by(
        employee_id=current_user_id,
        date=req_date,
        status="Pending"
    ).first()
    if duplicate:
        return jsonify({"error": "A duplicate Pending regularization request already exists for this date."}), 409

    # Check monthly request limit (all statuses: Pending, Approved, Rejected)
    # Count requests created in the current calendar month
    import datetime as dt
    company_today = _get_company_date()
    local_start = dt.datetime(company_today.year, company_today.month, 1, 0, 0, 0)
    kolkata_tz = dt.timezone(dt.timedelta(hours=5, minutes=30))
    start_of_month_utc = local_start.replace(tzinfo=kolkata_tz).astimezone(dt.timezone.utc).replace(tzinfo=None)

    monthly_count = AttendanceAdjustment.query.filter(
        AttendanceAdjustment.employee_id == current_user_id,
        AttendanceAdjustment.created_at >= start_of_month_utc
    ).count()

    if monthly_count >= 4:
        return jsonify({"error": "Monthly regularization limit (4 requests per month) has been reached."}), 429

    # Parse requested datetimes
    try:
        check_in_dt = _parse_regularization_datetime(check_in_str)
        check_out_dt = _parse_regularization_datetime(check_out_str)
    except ValueError as val_err:
        return jsonify({"error": str(val_err)}), 422

    if check_in_dt and check_out_dt and check_out_dt <= check_in_dt:
        return jsonify({"error": "Check-out time must be later than check-in time. Overnight shifts are currently not supported."}), 422

    # Store original attendance values
    existing_attendance = Attendance.query.filter_by(employee_id=current_user_id, date=req_date).first()
    orig_in = existing_attendance.check_in if existing_attendance else None
    orig_out = existing_attendance.check_out if existing_attendance else None

    # Create Adjustment Request
    req = AttendanceAdjustment(
        employee_id=current_user_id,
        date=req_date,
        check_in=check_in_dt,
        check_out=check_out_dt,
        original_check_in=orig_in,
        original_check_out=orig_out,
        reason=reason,
        status="Pending"
    )
    db.session.add(req)
    db.session.commit()

    # Notification to Admin
    try:
        employee = User.query.get(current_user_id)
        from utils.email_service import send_regularization_notification
        admin_email = current_app.config.get("ADMIN_NOTIFY_EMAIL", "admin@hrportal.com")
        send_regularization_notification(
            employee_name=employee.name,
            employee_id=employee.employee_id,
            date_str=date_str,
            check_in_str=check_in_str,
            check_out_str=check_out_str,
            reason=reason,
            recipient=admin_email
        )
    except Exception as notify_err:
        current_app.logger.warning(f"Failed to send regularization email: {notify_err}")

    return jsonify({"message": "Regularization request submitted successfully.", "request": req.to_dict()}), 201


# ------------------------------------------------------------------
# GET /api/attendance/regularization/history
# ------------------------------------------------------------------
@attendance_bp.route("/regularization/history", methods=["GET"])
@jwt_required
def regularization_history(current_user_id, current_user_role):
    """
    Get regularization requests history.
    - Admin: view all requests.
    - Employee: view own requests.
    """
    if current_user_role == "Admin":
        history = AttendanceAdjustment.query.order_by(AttendanceAdjustment.created_at.desc()).all()
    else:
        history = AttendanceAdjustment.query.filter_by(employee_id=current_user_id).order_by(AttendanceAdjustment.created_at.desc()).all()

    return jsonify([req.to_dict() for req in history]), 200


# ------------------------------------------------------------------
# POST /api/attendance/regularization/<int:id>/action
# ------------------------------------------------------------------
@attendance_bp.route("/regularization/<int:id>/action", methods=["POST"])
@admin_required
def action_regularization(id, current_user_id, current_user_role):
    """
    Action (Approve/Reject) an attendance regularization request.
    Only accessible by Admin.
    """
    req = AttendanceAdjustment.query.get(id)
    if not req:
        return jsonify({"error": "Regularization request not found."}), 404

    employee = User.query.get(req.employee_id)
    if not employee or not employee.is_active:
        return jsonify({"error": "Cannot approve regularization for inactive employees."}), 400

    if req.employee_id == current_user_id:
        return jsonify({"error": "Access denied. You cannot approve your own regularization request."}), 403

    if req.status != "Pending":
        return jsonify({"error": "This request has already been actioned."}), 400

    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body must be JSON."}), 400

    status = data.get("status")
    comment = data.get("comment", "").strip()

    if status not in ["Approved", "Rejected"]:
        return jsonify({"error": "Invalid action status. Must be 'Approved' or 'Rejected'."}), 422

    req.status = status
    req.approval_comment = comment if comment else None
    req.actioned_by = current_user_id
    req.actioned_at = datetime.utcnow()

    # Approved logic: Update or Create Attendance Record
    if status == "Approved":
        if req.check_in and req.check_out and req.check_out <= req.check_in:
            return jsonify({"error": "Check-out time must be later than check-in time. Overnight shifts are currently not supported."}), 422

        attendance = Attendance.query.filter_by(employee_id=req.employee_id, date=req.date).first()
        if attendance:
            # Update existing record
            attendance.check_in = req.check_in
            attendance.check_out = req.check_out
            attendance.calculate_hours()
        else:
            # Create new record ONLY when BOTH check_in and check_out are provided
            if req.check_in and req.check_out:
                new_att = Attendance(
                    employee_id=req.employee_id,
                    date=req.date,
                    check_in=req.check_in,
                    check_out=req.check_out
                )
                new_att.calculate_hours()
                db.session.add(new_att)
            else:
                current_app.logger.warning(
                    f"Approved regularization request {id} omitted creating attendance: missing check_in/out pair."
                )

    db.session.commit()

    # Notification to Employee
    try:
        employee = User.query.get(req.employee_id)
        from utils.email_service import send_regularization_notification
        send_regularization_notification(
            employee_name=employee.name,
            employee_id=employee.employee_id,
            date_str=req.date.isoformat(),
            check_in_str=None,
            check_out_str=None,
            reason=req.reason,
            recipient=employee.email,
            status=status,
            comment=comment
        )
    except Exception as notify_err:
        current_app.logger.warning(f"Failed to send action email update: {notify_err}")

    return jsonify({"message": f"Regularization request marked as {status}.", "request": req.to_dict()}), 200


# ------------------------------------------------------------------
# GET /api/attendance/team  (Supervisor direct reports attendance)
# ------------------------------------------------------------------
@attendance_bp.route("/team", methods=["GET"])
@jwt_required
def get_team_attendance(current_user_id, current_user_role):
    """
    Supervisor view of attendance records of their direct reports.
    """
    reports = User.query.filter_by(manager_id=current_user_id, is_active=True).all()
    if not reports:
        return jsonify([]), 200
    report_ids = [r.id for r in reports]

    date_str = request.args.get("date")
    month_str = request.args.get("month")

    query = Attendance.query.filter(Attendance.employee_id.in_(report_ids))
    if date_str:
        try:
            d = datetime.strptime(date_str, "%Y-%m-%d").date()
            query = query.filter(Attendance.date == d)
        except ValueError:
            return jsonify({"error": "Invalid date format. Use YYYY-MM-DD."}), 400
    elif month_str:
        try:
            year, month = map(int, month_str.split("-"))
            query = query.filter(
                db.extract('year', Attendance.date) == year,
                db.extract('month', Attendance.date) == month
            )
        except ValueError:
            return jsonify({"error": "Invalid month format. Use YYYY-MM."}), 400

    records = query.order_by(Attendance.date.desc(), Attendance.check_in.desc()).all()
    serialized = []
    for r in records:
        d = r.to_dict()
        d["attendance_status"] = r.get_status()
        serialized.append(d)

    return jsonify(serialized), 200




