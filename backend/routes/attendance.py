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
from models import Attendance, User, SystemSetting
from extensions import db
from utils.decorators import jwt_required, admin_required
from utils.geo import is_within_office_radius

attendance_bp = Blueprint("attendance", __name__)


# ------------------------------------------------------------------
# GET /api/attendance/status
# ------------------------------------------------------------------
@attendance_bp.route("/status", methods=["GET"])
@jwt_required
def today_status(current_user_id, current_user_role):
    """Return the current employee's attendance record for today."""
    today = date.today()
    record = Attendance.query.filter_by(employee_id=current_user_id, date=today).first()

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

    today = date.today()
    existing = Attendance.query.filter_by(employee_id=current_user_id, date=today).first()

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
    today = date.today()
    record = Attendance.query.filter_by(employee_id=current_user_id, date=today).first()

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


