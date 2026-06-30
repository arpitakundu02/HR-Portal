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
from routes.holidays import holidays_bp
from routes.approvals import approvals_bp
from routes.profile import profile_bp
from routes.notifications import notifications_bp
from routes.announcements import announcements_bp
from routes.work_transfers import work_transfers_bp
from routes.registrations import registrations_bp
from routes.comp_off import comp_off_bp
from routes.timesheets import timesheets_bp
from routes.team_dashboard import team_dashboard_bp
from routes.hierarchy import hierarchy_bp
from routes.policies import policies_bp


def create_app(config_class=Config) -> Flask:
    """Application factory pattern."""
    app = Flask(__name__)
    app.config.from_object(config_class)

    # ------------------------------------------------------------------ #
    # Extensions
    # ------------------------------------------------------------------ #
    db.init_app(app)

    # Configure CORS dynamically using FRONTEND_URL environment variable
    allowed_origins = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5000",
        "http://127.0.0.1:5000",
        "https://hr-portal-zbnv.vercel.app"
    ]
    frontend_url = os.environ.get("FRONTEND_URL")
    if frontend_url:
        allowed_origins.append(frontend_url.strip().rstrip("/"))

    CORS(
        app,
        resources={
            r"/api/*": {
                "origins": allowed_origins,
                "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
                "allow_headers": ["Content-Type", "Authorization"],
                "supports_credentials": True
            }
        }
    )

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
    app.register_blueprint(holidays_bp,    url_prefix="/api/holidays")
    app.register_blueprint(approvals_bp,   url_prefix="/api/approvals")
    app.register_blueprint(profile_bp,     url_prefix="/api/profile")
    app.register_blueprint(notifications_bp, url_prefix="/api/notifications")
    app.register_blueprint(announcements_bp, url_prefix="/api/announcements")
    app.register_blueprint(work_transfers_bp, url_prefix="/api/work-transfers")
    app.register_blueprint(registrations_bp, url_prefix="/api/registrations")
    app.register_blueprint(comp_off_bp,    url_prefix="/api/comp-off")
    app.register_blueprint(timesheets_bp,  url_prefix="/api/timesheets")
    app.register_blueprint(team_dashboard_bp, url_prefix="/api/team-dashboard")
    app.register_blueprint(hierarchy_bp,       url_prefix="/api/hierarchy")
    app.register_blueprint(policies_bp,        url_prefix="/api/policies")

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
