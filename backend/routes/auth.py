"""
backend/routes/auth.py
-----------------------
Authentication endpoints:
  POST /api/auth/login    - Authenticate and return JWT
  GET  /api/auth/me       - Return current user's profile

Employees cannot self-register.
Only Admin can create employee accounts (see employees.py).
"""

import jwt
import bcrypt
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, current_app
from models import User, LeaveBalance
from extensions import db
from utils.decorators import jwt_required

auth_bp = Blueprint("auth", __name__)


def _auto_employee_id() -> str:
    """Generate next sequential employee ID like HR-001."""
    last = User.query.order_by(User.id.desc()).first()
    next_num = (last.id + 1) if last else 1
    return f"HR-{next_num:03d}"



def _generate_token(user: User) -> str:
    """Generate a signed JWT for the given user."""
    payload = {
        "user_id": user.id,
        "role": user.role,
        "exp": datetime.utcnow() + timedelta(hours=current_app.config["JWT_EXP_DELTA_HOURS"]),
    }
    return jwt.encode(
        payload,
        current_app.config["JWT_SECRET_KEY"],
        algorithm=current_app.config["JWT_ALGORITHM"],
    )


# ------------------------------------------------------------------
# POST /api/auth/login
# ------------------------------------------------------------------
@auth_bp.route("/login", methods=["POST"])
def login():
    """
    Authenticate a user and return a JWT token.

    Request body:
        {
            "email": "admin@company.com",
            "password": "secret123"
        }

    Response (200):
        {
            "token": "<jwt>",
            "user": { ...profile }
        }
    """
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body must be JSON."}), 400

    email = data.get("email", "").strip().lower()
    password = data.get("password", "")
    role = data.get("role", "").strip()

    if not email or not password:
        return jsonify({"error": "Email and password are required."}), 400

    user = User.query.filter_by(email=email, is_active=True).first()
    if not user:
        return jsonify({"error": "Invalid credentials."}), 401

    # Verify requested role matches user's database role
    if role and user.role != role:
        return jsonify({"error": f"Access denied. Your account does not have {role} privileges."}), 403

    # Verify password against bcrypt hash
    if not bcrypt.checkpw(password.encode("utf-8"), user.password_hash.encode("utf-8")):
        return jsonify({"error": "Invalid credentials."}), 401

    token = _generate_token(user)

    # Send login notification email to account owner
    try:
        from utils.email_service import send_login_notification
        send_login_notification(email=user.email, recipient=user.email, name=user.name)
    except Exception:
        pass

    return jsonify({
        "token": token,
        "user": user.to_dict(include_sensitive=(user.role == "Admin")),
    }), 200


# ------------------------------------------------------------------
# GET /api/auth/me
# ------------------------------------------------------------------
@auth_bp.route("/me", methods=["GET"])
@jwt_required
def get_current_user(current_user_id, current_user_role):
    """Return the authenticated user's own profile."""
    user = User.query.get(current_user_id)
    if not user:
        return jsonify({"error": "User not found."}), 404

    return jsonify(user.to_dict(include_sensitive=True)), 200




