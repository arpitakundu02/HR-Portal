"""
backend/routes/holidays.py
--------------------------
Holiday management blueprint.
"""

from datetime import datetime, date
from flask import Blueprint, request, jsonify
from models import Holiday
from extensions import db
from utils.decorators import jwt_required, admin_required

holidays_bp = Blueprint("holidays", __name__)

# ------------------------------------------------------------------
# GET /api/holidays
# ------------------------------------------------------------------
@holidays_bp.route("", methods=["GET"])
@jwt_required
def get_all_holidays(current_user_id, current_user_role):
    """Retrieve all holidays with optional upcoming filtering and limits."""
    # Gracefully attempt to auto-populate Indian public holidays for current and next year
    try:
        import holidays
        current_year = date.today().year
        target_years = [current_year, current_year + 1]

        for year in target_years:
            # Check if any holidays already exist for this year
            year_exists = Holiday.query.filter(
                db.extract("year", Holiday.date) == year
            ).first()

            if not year_exists:
                # Generate Indian public holidays
                in_holidays = holidays.India(years=year)
                for h_date, h_name in sorted(in_holidays.items()):
                    # Respect unique constraint: double check if date is already in DB (just in case)
                    if not Holiday.query.filter_by(date=h_date).first():
                        db_holiday = Holiday(
                            name=h_name,
                            date=h_date,
                            description="Indian Public Holiday"
                        )
                        db.session.add(db_holiday)
                db.session.commit()
    except Exception as e:
        # Gracefully handle failures or absence of package without crashing API
        print(f"[ERROR] Failed to auto-generate holidays: {e}")

    upcoming = request.args.get("upcoming", "false").lower() == "true"
    limit_str = request.args.get("limit")

    query = Holiday.query

    if upcoming:
        today = date.today()
        query = query.filter(Holiday.date >= today).order_by(Holiday.date.asc())
    else:
        query = query.order_by(Holiday.date.desc())

    if limit_str:
        try:
            limit = int(limit_str)
            if limit > 0:
                query = query.limit(limit)
        except ValueError:
            pass

    records = query.all()
    return jsonify([h.to_dict() for h in records]), 200

# ------------------------------------------------------------------
# POST /api/holidays
# ------------------------------------------------------------------
@holidays_bp.route("", methods=["POST"])
@jwt_required
@admin_required
def create_holiday(current_user_id, current_user_role):
    """Create a new holiday (Admin only)."""
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body must be JSON."}), 400

    name = data.get("name")
    date_val_str = data.get("date")
    description = data.get("description")

    if not name or not name.strip():
        return jsonify({"error": "Holiday name is required."}), 400
    if not date_val_str:
        return jsonify({"error": "Holiday date is required."}), 400

    try:
        # Parse date yyyy-mm-dd
        date_val = datetime.strptime(date_val_str.split("T")[0], "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid date format. Expected YYYY-MM-DD."}), 400

    # Prevent duplicate holiday dates
    existing = Holiday.query.filter_by(date=date_val).first()
    if existing:
        return jsonify({"error": "A holiday is already scheduled on this date."}), 400

    holiday = Holiday(
        name=name.strip(),
        date=date_val,
        description=description.strip() if description else None
    )
    db.session.add(holiday)
    db.session.commit()

    return jsonify(holiday.to_dict()), 201

# ------------------------------------------------------------------
# PUT /api/holidays/<id>
# ------------------------------------------------------------------
@holidays_bp.route("/<int:holiday_id>", methods=["PUT"])
@jwt_required
@admin_required
def update_holiday(current_user_id, current_user_role, holiday_id):
    """Update an existing holiday (Admin only)."""
    holiday = Holiday.query.get(holiday_id)
    if not holiday:
        return jsonify({"error": "Holiday not found."}), 404

    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body must be JSON."}), 400

    name = data.get("name")
    date_val_str = data.get("date")
    description = data.get("description")

    if name is not None:
        if not name.strip():
            return jsonify({"error": "Holiday name is required."}), 400
        holiday.name = name.strip()

    if date_val_str is not None:
        try:
            date_val = datetime.strptime(date_val_str.split("T")[0], "%Y-%m-%d").date()
        except (ValueError, TypeError):
            return jsonify({"error": "Invalid date format. Expected YYYY-MM-DD."}), 400

        # Prevent duplicate holiday dates (exclude current record)
        existing = Holiday.query.filter(Holiday.date == date_val, Holiday.id != holiday_id).first()
        if existing:
            return jsonify({"error": "A holiday is already scheduled on this date."}), 400
        holiday.date = date_val

    if description is not None:
        holiday.description = description.strip() if description else None

    db.session.commit()
    return jsonify(holiday.to_dict()), 200

# ------------------------------------------------------------------
# DELETE /api/holidays/<id>
# ------------------------------------------------------------------
@holidays_bp.route("/<int:holiday_id>", methods=["DELETE"])
@jwt_required
@admin_required
def delete_holiday(current_user_id, current_user_role, holiday_id):
    """Delete a holiday (Admin only)."""
    holiday = Holiday.query.get(holiday_id)
    if not holiday:
        return jsonify({"error": "Holiday not found."}), 404

    db.session.delete(holiday)
    db.session.commit()
    return jsonify({"message": "Holiday deleted successfully."}), 200
