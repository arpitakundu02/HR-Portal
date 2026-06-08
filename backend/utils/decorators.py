"""
backend/utils/decorators.py
----------------------------
JWT authentication and Role-Based Access Control (RBAC) decorators.

Usage:
    @jwt_required          - Any authenticated user
    @admin_required        - Admin role only
    @self_or_admin(param)  - The resource owner or an Admin
"""

import jwt
from functools import wraps
from flask import request, jsonify, current_app


def _extract_token():
    """Extract Bearer token from the Authorization header."""
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return None
    return auth_header.split(" ", 1)[1]


def _decode_token(token):
    """Decode and validate a JWT. Returns payload or raises exception."""
    return jwt.decode(
        token,
        current_app.config["JWT_SECRET_KEY"],
        algorithms=[current_app.config["JWT_ALGORITHM"]],
    )


def jwt_required(f):
    """Decorator: ensures the request carries a valid JWT token.
    Injects `current_user_id` and `current_user_role` into the function kwargs.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        token = _extract_token()
        if not token:
            return jsonify({"error": "Authorization token is missing."}), 401
        try:
            payload = _decode_token(token)
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token has expired. Please log in again."}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token."}), 401

        kwargs["current_user_id"] = payload["user_id"]
        kwargs["current_user_role"] = payload["role"]
        return f(*args, **kwargs)

    return decorated


def admin_required(f):
    """Decorator: restricts endpoint to Admin role only.
    Must be used after @jwt_required.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        token = _extract_token()
        if not token:
            return jsonify({"error": "Authorization token is missing."}), 401
        try:
            payload = _decode_token(token)
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token has expired. Please log in again."}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token."}), 401

        if payload.get("role") != "Admin":
            return jsonify({"error": "Admin access required."}), 403

        kwargs["current_user_id"] = payload["user_id"]
        kwargs["current_user_role"] = payload["role"]
        return f(*args, **kwargs)

    return decorated


def self_or_admin(id_param="id"):
    """Decorator factory: allows access if the authenticated user is the resource
    owner (user_id matches the URL param) OR is an Admin.

    Args:
        id_param: The URL parameter name that holds the target user's id.
    """
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            token = _extract_token()
            if not token:
                return jsonify({"error": "Authorization token is missing."}), 401
            try:
                payload = _decode_token(token)
            except jwt.ExpiredSignatureError:
                return jsonify({"error": "Token has expired. Please log in again."}), 401
            except jwt.InvalidTokenError:
                return jsonify({"error": "Invalid token."}), 401

            current_id = payload["user_id"]
            current_role = payload["role"]
            target_id = kwargs.get(id_param)

            if current_role != "Admin" and str(current_id) != str(target_id):
                return jsonify({"error": "Access denied. You can only access your own data."}), 403

            kwargs["current_user_id"] = current_id
            kwargs["current_user_role"] = current_role
            return f(*args, **kwargs)

        return decorated
    return decorator
