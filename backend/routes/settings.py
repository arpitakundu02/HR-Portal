# backend/routes/settings.py
"""
backend/routes/settings.py
--------------------------
Blueprint for managing System Settings. Admin only.
"""

from datetime import datetime
from flask import Blueprint, request, jsonify
from models import SystemSetting, User
from extensions import db
from utils.decorators import admin_required

settings_bp = Blueprint("settings", __name__)

@settings_bp.route("", methods=["GET"])
@admin_required
def get_all_settings(current_user_id, current_user_role):
    """Retrieve all system settings as a key-value dictionary."""
    settings = SystemSetting.query.all()
    data = {s.key: s.value for s in settings}
    return jsonify(data), 200

@settings_bp.route("", methods=["POST"])
@admin_required
def update_system_settings(current_user_id, current_user_role):
    """Update system settings with input validation."""
    data = request.get_json(silent=True) or {}
    
    admin = User.query.get(current_user_id)
    admin_name = admin.name if admin else "Admin"

    # Validation errors dictionary
    validation_errors = {}

    # 1. Geofence validations
    if "office_latitude" in data:
        try:
            lat = float(data["office_latitude"])
            if not (-90 <= lat <= 90):
                validation_errors["office_latitude"] = "Latitude must be between -90 and 90."
        except (ValueError, TypeError):
            validation_errors["office_latitude"] = "Latitude must be a valid decimal number."

    if "office_longitude" in data:
        try:
            lon = float(data["office_longitude"])
            if not (-180 <= lon <= 180):
                validation_errors["office_longitude"] = "Longitude must be between -180 and 180."
        except (ValueError, TypeError):
            validation_errors["office_longitude"] = "Longitude must be a valid decimal number."

    if "office_radius_meters" in data:
        try:
            rad = float(data["office_radius_meters"])
            if rad <= 0:
                validation_errors["office_radius_meters"] = "Radius must be greater than 0."
        except (ValueError, TypeError):
            validation_errors["office_radius_meters"] = "Radius must be a valid positive number."

    # 2. Leave Settings validations
    if "apl_allocation" in data:
        try:
            apl = int(data["apl_allocation"])
            if apl < 0:
                validation_errors["apl_allocation"] = "APL allocation must be 0 or greater."
        except (ValueError, TypeError):
            validation_errors["apl_allocation"] = "APL allocation must be an integer."

    if "wfh_limit_male" in data:
        try:
            wfh_m = int(data["wfh_limit_male"])
            if wfh_m < 0:
                validation_errors["wfh_limit_male"] = "WFH male limit must be 0 or greater."
        except (ValueError, TypeError):
            validation_errors["wfh_limit_male"] = "WFH male limit must be an integer."

    if "wfh_limit_female" in data:
        try:
            wfh_f = int(data["wfh_limit_female"])
            if wfh_f < 0:
                validation_errors["wfh_limit_female"] = "WFH female limit must be 0 or greater."
        except (ValueError, TypeError):
            validation_errors["wfh_limit_female"] = "WFH female limit must be an integer."

    # 3. Security Settings validations
    if "min_password_length" in data:
        try:
            min_pwd = int(data["min_password_length"])
            if min_pwd < 6:
                validation_errors["min_password_length"] = "Minimum password length must be at least 6."
        except (ValueError, TypeError):
            validation_errors["min_password_length"] = "Minimum password length must be an integer."

    if "session_timeout" in data:
        try:
            timeout = int(data["session_timeout"])
            if timeout <= 0:
                validation_errors["session_timeout"] = "Session timeout must be greater than 0."
        except (ValueError, TypeError):
            validation_errors["session_timeout"] = "Session timeout must be an integer."

    # 4. Attendance Settings validations
    if "standard_working_hours" in data:
        try:
            std_hrs = float(data["standard_working_hours"])
            if not (1 <= std_hrs <= 24):
                validation_errors["standard_working_hours"] = "Standard working hours must be between 1 and 24."
        except (ValueError, TypeError):
            validation_errors["standard_working_hours"] = "Standard working hours must be a valid number."

    if validation_errors:
        return jsonify({"errors": validation_errors, "error": "Validation failed."}), 422

    # Save to DB
    updated_keys = []
    for key, val in data.items():
        if key in ["office_updated_by_name", "office_updated_at"]:
            continue
            
        setting = SystemSetting.query.filter_by(key=key).first()
        val_str = str(val).strip()
        if setting:
            setting.value = val_str
        else:
            setting = SystemSetting(key=key, value=val_str)
            db.session.add(setting)
        updated_keys.append(key)

    # Log audit trail if geofence updated
    geofence_keys = ["office_latitude", "office_longitude", "office_radius_meters"]
    if any(k in updated_keys for k in geofence_keys):
        settings_meta = {
            "office_updated_by_name": admin_name,
            "office_updated_at": datetime.utcnow().isoformat()
        }
        for key, val in settings_meta.items():
            setting = SystemSetting.query.filter_by(key=key).first()
            if setting:
                setting.value = val
            else:
                setting = SystemSetting(key=key, value=val)
                db.session.add(setting)

    db.session.commit()

    all_settings = SystemSetting.query.all()
    return jsonify({s.key: s.value for s in all_settings}), 200
