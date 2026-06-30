"""
backend/config.py
-----------------
Centralised application configuration.
All sensitive values are loaded from environment variables via python-dotenv.
Never hard-code credentials here.
"""

import os
from dotenv import load_dotenv

# Load .env file if present (development convenience)
load_dotenv()


class Config:
    # ------------------------------------------------------------------ #
    # Flask Core
    # ------------------------------------------------------------------ #
    SECRET_KEY: str = os.environ.get("SECRET_KEY", "change_me")
    DEBUG: bool = os.environ.get("FLASK_ENV", "production") == "development"

    # ------------------------------------------------------------------ #
    # JWT
    # ------------------------------------------------------------------ #
    JWT_SECRET_KEY: str = os.environ.get("JWT_SECRET_KEY", "change_me_jwt")
    JWT_ALGORITHM: str = "HS256"
    JWT_EXP_DELTA_HOURS: int = 12  # Token validity window

    # ------------------------------------------------------------------ #
    # MySQL / SQLAlchemy
    # ------------------------------------------------------------------ #
    DB_HOST: str = os.environ.get("DB_HOST") or os.environ.get("MYSQLHOST") or "localhost"
    DB_USER: str = os.environ.get("DB_USER") or os.environ.get("MYSQLUSER") or "root"
    DB_PASSWORD: str = os.environ.get("DB_PASSWORD") or os.environ.get("MYSQLPASSWORD") or ""
    DB_NAME: str = os.environ.get("DB_NAME") or os.environ.get("MYSQLDATABASE") or "hr_portal"
    DB_PORT: str = os.environ.get("DB_PORT") or os.environ.get("MYSQLPORT") or "3306"

    # Configured dynamically via environment variables
    SQLALCHEMY_DATABASE_URI: str = (
        f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}"
        f"@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False

    # ------------------------------------------------------------------ #
    # File Uploads (Resumes)
    # ------------------------------------------------------------------ #
    UPLOAD_FOLDER: str = os.path.join(os.path.dirname(__file__), "uploads")
    ALLOWED_EXTENSIONS: set = {"pdf", "doc", "docx"}
    MAX_CONTENT_LENGTH: int = 5 * 1024 * 1024  # 5 MB max upload size

    # ------------------------------------------------------------------ #
    # SMTP Email Notifications
    # ------------------------------------------------------------------ #
    SMTP_HOST: str = os.environ.get("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT: int = int(os.environ.get("SMTP_PORT", 587))
    SMTP_USER: str = os.environ.get("SMTP_USER", os.environ.get("SMTP_USERNAME", ""))
    SMTP_PASSWORD: str = os.environ.get("SMTP_PASSWORD", "")
    SMTP_FROM: str = os.environ.get("SMTP_FROM", os.environ.get("SMTP_SENDER_EMAIL", "noreply@hrportal.com"))
    ADMIN_NOTIFY_EMAIL: str = os.environ.get("ADMIN_NOTIFY_EMAIL", "admin@hrportal.com")

    # ------------------------------------------------------------------ #
    # Office Geolocation (for Attendance Radius Check)
    # ------------------------------------------------------------------ #
    OFFICE_LATITUDE: float = float(os.environ.get("OFFICE_LATITUDE", 28.6139))
    OFFICE_LONGITUDE: float = float(os.environ.get("OFFICE_LONGITUDE", 77.2090))
    OFFICE_RADIUS_METERS: float = float(os.environ.get("OFFICE_RADIUS_METERS", 200))
