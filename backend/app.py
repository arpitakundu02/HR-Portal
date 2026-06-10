"""
backend/app.py
--------------
Flask application factory and entry point.
Registers all blueprints, configures CORS, and initialises extensions.
"""

import os
from flask import Flask, jsonify
from flask_cors import CORS

from config import Config
from extensions import db

# Import blueprints
from routes.auth import auth_bp
from routes.employees import employees_bp
from routes.departments import departments_bp
from routes.leaves import leaves_bp
from routes.attendance import attendance_bp
from routes.meetings import meetings_bp
from routes.tasks import tasks_bp
from routes.exports import exports_bp


def create_app(config_class=Config) -> Flask:
    """Application factory pattern."""
    app = Flask(__name__)
    app.config.from_object(config_class)

    # ------------------------------------------------------------------ #
    # Extensions
    # ------------------------------------------------------------------ #
    db.init_app(app)

    # Allow all origins in dev; restrict to your frontend domain in production
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # ------------------------------------------------------------------ #
    # Ensure uploads directory exists
    # ------------------------------------------------------------------ #
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    # ------------------------------------------------------------------ #
    # Register blueprints
    # ------------------------------------------------------------------ #
    app.register_blueprint(auth_bp,        url_prefix="/api/auth")
    app.register_blueprint(employees_bp,   url_prefix="/api/employees")
    app.register_blueprint(departments_bp, url_prefix="/api/departments")
    app.register_blueprint(leaves_bp,      url_prefix="/api/leaves")
    app.register_blueprint(attendance_bp,  url_prefix="/api/attendance")
    app.register_blueprint(meetings_bp,    url_prefix="/api/meetings")
    app.register_blueprint(tasks_bp,       url_prefix="/api/tasks")
    app.register_blueprint(exports_bp,     url_prefix="/api/exports")

    # ------------------------------------------------------------------ #
    # Health check
    # ------------------------------------------------------------------ #
    @app.route("/api/health", methods=["GET"])
    def health():
        return jsonify({"status": "ok", "message": "HR Portal API is running."}), 200

    # ------------------------------------------------------------------ #
    # Global 404 / 405 handlers
    # ------------------------------------------------------------------ #
    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "The requested resource was not found."}), 404

    @app.errorhandler(405)
    def method_not_allowed(e):
        return jsonify({"error": "Method not allowed."}), 405

    @app.errorhandler(413)
    def request_entity_too_large(e):
        return jsonify({"error": "Uploaded file exceeds the 5 MB size limit."}), 413

    return app


# ------------------------------------------------------------------ #
# Entry point
# ------------------------------------------------------------------ #
if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=app.config["DEBUG"])
