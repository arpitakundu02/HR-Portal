"""
backend/routes/tasks.py
------------------------
Task assignment and tracking.

Endpoints:
  GET  /api/tasks          - Employee: own tasks; Admin: all tasks (filterable)
  POST /api/tasks          - Admin: Assign a task to an employee
  PUT  /api/tasks/<id>     - Admin or assigned employee: Update task status/details
  DELETE /api/tasks/<id>   - Admin: Delete a task
"""

from datetime import datetime
from flask import Blueprint, request, jsonify, current_app
from models import Task, User
from extensions import db
from utils.decorators import jwt_required, admin_required
from utils.email_service import send_task_notification

tasks_bp = Blueprint("tasks", __name__)

VALID_STATUSES = ("Pending", "In Progress", "Completed")


# ------------------------------------------------------------------
# GET /api/tasks
# ------------------------------------------------------------------
@tasks_bp.route("/", methods=["GET"])
@jwt_required
def list_tasks(current_user_id, current_user_role):
    """
    Return tasks.
    - Employee: Only tasks assigned to them.
    - Admin: All tasks, optionally filtered by ?employee_id=, ?status=

    Query params:
        employee_id (int) - Admin only: filter by assignee
        status      (str) - Filter by status (Pending | In Progress | Completed)
        page        (int) - Page number (default 1)
        per_page    (int) - Results per page (default 20)
    """
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)

    if current_user_role == "Admin":
        query = Task.query
        if emp_id := request.args.get("employee_id", type=int):
            query = query.filter_by(employee_id=emp_id)
    else:
        from datetime import date
        from models import WorkTransferRequest
        today = date.today()
        # Find users who have actively delegated tasks to the current user
        delegated_users = db.session.query(WorkTransferRequest.requester_id).filter(
            WorkTransferRequest.delegate_to_id == current_user_id,
            WorkTransferRequest.status == "Approved",
            WorkTransferRequest.start_date <= today,
            WorkTransferRequest.end_date >= today,
            WorkTransferRequest.transfer_tasks == True
        ).all()
        delegator_ids = [r[0] for r in delegated_users]
        
        if delegator_ids:
            query = Task.query.filter(
                db.or_(
                    Task.employee_id == current_user_id,
                    Task.employee_id.in_(delegator_ids)
                )
            )
        else:
            query = Task.query.filter(Task.employee_id == current_user_id)

    if status := request.args.get("status"):
        if status not in VALID_STATUSES:
            return jsonify({"error": f"status must be one of: {', '.join(VALID_STATUSES)}"}), 422
        query = query.filter_by(status=status)

    pagination = query.order_by(Task.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return jsonify({
        "tasks": [t.to_dict() for t in pagination.items],
        "total": pagination.total,
        "page": page,
        "pages": pagination.pages,
    }), 200

# ------------------------------------------------------------------
# GET /api/tasks/stats
# ------------------------------------------------------------------
@tasks_bp.route("/stats", methods=["GET"])
@admin_required
def get_task_stats(current_user_id, current_user_role):
    """
    Get aggregated task statistics for the dashboard.
    Returns count distribution of tasks grouped by status for active employees only.
    """
    from sqlalchemy import func
    from models import User
    
    # Query status distribution for tasks assigned to active employees
    results = db.session.query(
        Task.status,
        func.count(Task.id)
    ).join(
        User, Task.employee_id == User.id
    ).filter(
        User.is_active == True
    ).group_by(
        Task.status
    ).all()
    
    status_distribution = {
        "Pending": 0,
        "In Progress": 0,
        "Completed": 0
    }
    
    for status, count in results:
        if status in status_distribution:
            status_distribution[status] = count
            
    return jsonify({
        "status_distribution": status_distribution
    }), 200


# ------------------------------------------------------------------
# POST /api/tasks
# ------------------------------------------------------------------
@tasks_bp.route("/", methods=["POST"])
@admin_required
def create_task(current_user_id, current_user_role):
    """
    Admin-only: Assign a new task to an employee.

    Request body:
        {
            "title": "Prepare Q3 Report",
            "description": "Compile all regional data",
            "employee_id": 5,
            "due_date": "2025-08-31",      // optional
            "status": "Pending"             // optional, default Pending
        }
    """
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body must be JSON."}), 400

    if not data.get("title") or not data.get("employee_id"):
        return jsonify({"error": "'title' and 'employee_id' are required."}), 422

    employee = User.query.get(data["employee_id"])
    if not employee or not employee.is_active:
        return jsonify({"error": "Employee not found or inactive."}), 404

    due_date = None
    if data.get("due_date"):
        try:
            due_date = datetime.strptime(data["due_date"], "%Y-%m-%d").date()
        except ValueError:
            return jsonify({"error": "due_date must be in YYYY-MM-DD format."}), 422

    status = data.get("status", "Pending")
    if status not in VALID_STATUSES:
        return jsonify({"error": f"status must be one of: {', '.join(VALID_STATUSES)}"}), 422

    task = Task(
        title=data["title"].strip(),
        description=data.get("description"),
        employee_id=data["employee_id"],
        status=status,
        due_date=due_date,
        assigned_by=current_user_id,
    )
    db.session.add(task)
    db.session.commit()

    # Send email notification to employee
    try:
        send_task_notification(
            task_name=task.title,
            description=task.description,
            priority=data.get("priority", "Normal"),
            due_date=data.get("due_date", "No due date"),
            recipient=employee.email,
            employee_name=employee.name,
            is_completed=False
        )
    except Exception:
        pass

    # Create in-app Notification entry for tasks integration
    from utils.notification_service import create_notification
    try:
        create_notification(
            user_id=task.employee_id,
            title="New Task Assigned",
            content=f"You have been assigned a new task: {task.title}",
            notification_type="Task",
            target_id=task.id,
            action_url="/tasks"
        )
    except Exception:
        pass

    return jsonify(task.to_dict()), 201


# ------------------------------------------------------------------
# PUT /api/tasks/<id>
# ------------------------------------------------------------------
@tasks_bp.route("/<int:task_id>", methods=["PUT"])
@jwt_required
def update_task(task_id, current_user_id, current_user_role):
    """
    Update a task.
    - Admin: Can update any field.
    - Employee: Can only update the status of their own assigned task.
    """
    task = Task.query.get_or_404(task_id)

    # Employees can only update their own tasks' status or delegated tasks
    is_authorized = (current_user_role == "Admin" or task.employee_id == current_user_id)
    if not is_authorized:
        from datetime import date
        from models import WorkTransferRequest
        today = date.today()
        is_authorized = db.session.query(db.exists().where(db.and_(
            WorkTransferRequest.requester_id == task.employee_id,
            WorkTransferRequest.delegate_to_id == current_user_id,
            WorkTransferRequest.status == "Approved",
            WorkTransferRequest.start_date <= today,
            WorkTransferRequest.end_date >= today,
            WorkTransferRequest.transfer_tasks == True
        ))).scalar()
        
    if not is_authorized:
        return jsonify({"error": "Access denied. You can only update your own or delegated tasks."}), 403

    data = request.get_json(silent=True) or {}

    if current_user_role == "Admin":
        if "title" in data:
            task.title = data["title"].strip()
        if "description" in data:
            task.description = data["description"]
        if "employee_id" in data:
            task.employee_id = data["employee_id"]
        if "due_date" in data:
            try:
                task.due_date = datetime.strptime(data["due_date"], "%Y-%m-%d").date()
            except ValueError:
                return jsonify({"error": "due_date must be in YYYY-MM-DD format."}), 422

    # Both Admin and Employee can update status
    if "status" in data:
        if data["status"] not in VALID_STATUSES:
            return jsonify({"error": f"status must be one of: {', '.join(VALID_STATUSES)}"}), 422
        task.status = data["status"]

    db.session.commit()

    # Send email notification if task is marked complete
    if "status" in data and data["status"] == "Completed":
        try:
            employee = User.query.get(task.employee_id)
            send_task_notification(
                task_name=task.title,
                description=task.description,
                priority=None,
                due_date=None,
                recipient=current_app.config["ADMIN_NOTIFY_EMAIL"],
                employee_name=employee.name,
                is_completed=True
            )
        except Exception:
            pass

    return jsonify(task.to_dict()), 200


# ------------------------------------------------------------------
# DELETE /api/tasks/<id>
# ------------------------------------------------------------------
@tasks_bp.route("/<int:task_id>", methods=["DELETE"])
@admin_required
def delete_task(task_id, current_user_id, current_user_role):
    """Admin-only: Delete a task."""
    task = Task.query.get_or_404(task_id)
    db.session.delete(task)
    db.session.commit()
    return jsonify({"message": f"Task '{task.title}' deleted."}), 200
