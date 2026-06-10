# backend/utils/employee_helpers.py
"""
Utility helper functions for retrieving manager hierarchy structures.
"""

from models import User

def get_direct_reports(user_id):
    """
    Retrieve all active direct reports for the given user_id.
    """
    user = User.query.get(user_id)
    if user:
        return user.reports.filter_by(is_active=True).all()
    return []

def get_manager(user_id):
    """
    Retrieve the manager of the given user_id.
    """
    user = User.query.get(user_id)
    if user:
        return user.manager
    return None
