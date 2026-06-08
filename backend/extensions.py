"""
backend/extensions.py
----------------------
Shared Flask extension instances.
Centralising them here prevents circular imports between app.py, models.py, and routes.
"""

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
