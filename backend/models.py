"""
backend/models.py
-----------------
SQLAlchemy ORM models for the HR Portal.
Covers: Users, Departments, LeaveBalance, Leave, Attendance, Meeting, Task.
"""

from datetime import datetime
from extensions import db


# ============================================================
# Department
# ============================================================
class Department(db.Model):
    __tablename__ = "departments"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
    manager_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    employees = db.relationship("User", back_populates="department", lazy="dynamic", foreign_keys="User.department_id")
    meetings = db.relationship("Meeting", back_populates="department", lazy="dynamic")
    manager = db.relationship("User", foreign_keys=[manager_id])

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "manager_id": self.manager_id,
            "manager_name": self.manager.name if self.manager else None,
            "created_at": self.created_at.isoformat(),
        }


# ============================================================
# User  (Authentication + Employee Profile combined)
# ============================================================
class User(db.Model):
    __tablename__ = "users"
    __table_args__ = (
        db.Index("idx_users_active_dept", "is_active", "department_id"),
    )

    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.String(50), unique=True, nullable=False)  # e.g. HR-001
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.Enum("Admin", "Employee"), default="Employee", nullable=False)

    # Personal details
    name = db.Column(db.String(100), nullable=False)
    fathers_name = db.Column(db.String(100), nullable=True)
    dob = db.Column(db.Date, nullable=True)
    blood_group = db.Column(db.String(10), nullable=True)

    # Address
    address = db.Column(db.Text, nullable=True)
    permanent_address = db.Column(db.Text, nullable=True)
    current_address = db.Column(db.Text, nullable=True)
    emergency_contact = db.Column(db.String(50), nullable=True)

    # Employment
    department_id = db.Column(db.Integer, db.ForeignKey("departments.id"), nullable=True)
    date_of_joining = db.Column(db.Date, nullable=True)
    salary = db.Column(db.Numeric(10, 2), nullable=True)
    rank = db.Column(db.String(50), nullable=True)
    manager_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    is_line_manager = db.Column(db.Boolean, default=False, nullable=False)

    # Documents
    aadhar_number = db.Column(db.String(20), nullable=True)
    resume_url = db.Column(db.String(255), nullable=True)
    photo_url = db.Column(db.String(255), nullable=True)
    phone_number = db.Column(db.String(20), nullable=True)
    bio = db.Column(db.Text, nullable=True)
    experience_summary = db.Column(db.Text, nullable=True)
    gender = db.Column(db.String(20), default='Male', nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    deleted_at = db.Column(db.DateTime, nullable=True)
    deleted_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)

    # Relationships
    department = db.relationship("Department", back_populates="employees", foreign_keys=[department_id])
    manager = db.relationship("User", remote_side=[id], foreign_keys=[manager_id], backref=db.backref("reports", lazy="dynamic", foreign_keys=[manager_id]))
    leave_balances = db.relationship("LeaveBalance", back_populates="employee", lazy="dynamic", cascade="all, delete-orphan")
    leaves = db.relationship("Leave", foreign_keys="Leave.employee_id", back_populates="employee", lazy="dynamic", cascade="all, delete-orphan")
    attendance_records = db.relationship("Attendance", back_populates="employee", lazy="dynamic", cascade="all, delete-orphan")
    tasks = db.relationship("Task", foreign_keys="Task.employee_id", back_populates="employee", lazy="dynamic", cascade="all, delete-orphan")

    def to_dict(self, include_sensitive=False):
        data = {
            "id": self.id,
            "employee_id": self.employee_id,
            "email": self.email,
            "role": self.role,
            "name": self.name,
            "fathers_name": self.fathers_name,
            "dob": self.dob.isoformat() if self.dob else None,
            "blood_group": self.blood_group,
            "address": self.address,
            "permanent_address": self.permanent_address,
            "current_address": self.current_address,
            "emergency_contact": self.emergency_contact,
            "phone_number": self.phone_number,
            "department_id": self.department_id,
            "department_name": self.department.name if self.department else None,
            "date_of_joining": self.date_of_joining.isoformat() if self.date_of_joining else None,
            "rank": self.rank,
            "manager_id": self.manager_id,
            "manager_name": self.manager.name if self.manager else None,
            "is_line_manager": self.is_line_manager,
            "resume_url": self.resume_url,
            "photo_url": self.photo_url,
            "bio": self.bio,
            "experience_summary": self.experience_summary,
            "gender": self.gender,
            "is_active": self.is_active,
            "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
            "deleted_by": self.deleted_by,
            "created_at": self.created_at.isoformat(),
        }
        if include_sensitive:
            # Only exposed to Admin or self
            data["salary"] = float(self.salary) if self.salary else None
            data["aadhar_number"] = self.aadhar_number
        return data


# ============================================================
# Leave Balance
# ============================================================
class LeaveBalance(db.Model):
    __tablename__ = "leave_balances"

    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    leave_type = db.Column(db.Enum("APL", "WFH"), nullable=False)
    allocated = db.Column(db.Integer, default=0)
    used = db.Column(db.Integer, default=0)
    # remaining = allocated - used; may be negative (overdraft leave supported)
    remaining = db.Column(db.Integer, default=0)

    # Constraints
    __table_args__ = (
        db.UniqueConstraint("employee_id", "leave_type", name="uq_employee_leave_type"),
    )

    # Relationships
    employee = db.relationship("User", back_populates="leave_balances")

    def recalculate(self):
        """Recalculate remaining = allocated - used. Negative values allowed."""
        self.remaining = self.allocated - self.used

    def to_dict(self):
        return {
            "id": self.id,
            "employee_id": self.employee_id,
            "leave_type": self.leave_type,
            "allocated": self.allocated,
            "used": self.used,
            "remaining": self.remaining,
        }


# ============================================================
# Leave Request
# ============================================================
class Leave(db.Model):
    __tablename__ = "leaves"

    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    leave_type = db.Column(db.Enum("APL", "WFH"), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    reason = db.Column(db.Text, nullable=True)
    status = db.Column(db.Enum("Pending", "Approved", "Rejected"), default="Pending", index=True)
    actioned_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    actioned_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    responsibility_transfer_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)

    # Relationships
    employee = db.relationship("User", foreign_keys=[employee_id], back_populates="leaves")
    responsibility_transfer = db.relationship("User", foreign_keys=[responsibility_transfer_id])
    actioned_by_user = db.relationship("User", foreign_keys=[actioned_by])

    @property
    def days_requested(self):
        delta = self.end_date - self.start_date
        return delta.days + 1

    def to_dict(self):
        return {
            "id": self.id,
            "employee_id": self.employee_id,
            "employee_name": self.employee.name if self.employee else None,
            "leave_type": self.leave_type,
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat(),
            "days_requested": self.days_requested,
            "reason": self.reason,
            "status": self.status,
            "responsibility_transfer_id": self.responsibility_transfer_id,
            "responsibility_transfer_name": self.responsibility_transfer.name if self.responsibility_transfer else None,
            "actioned_by": self.actioned_by,
            "actioned_at": (self.actioned_at.isoformat() + "Z") if self.actioned_at else None,
            "created_at": self.created_at.isoformat() + "Z",
        }


# ============================================================
# Attendance
# ============================================================
class Attendance(db.Model):
    __tablename__ = "attendance"

    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    date = db.Column(db.Date, nullable=False)
    check_in = db.Column(db.DateTime, nullable=True)
    check_out = db.Column(db.DateTime, nullable=True)
    working_hours = db.Column(db.Numeric(5, 2), default=0.00)
    latitude = db.Column(db.Float, nullable=True)   # Check-in latitude
    longitude = db.Column(db.Float, nullable=True)  # Check-in longitude

    __table_args__ = (
        db.UniqueConstraint("employee_id", "date", name="uq_employee_date"),
        db.Index("idx_attendance_date_checkin", "date", "check_in"),
    )

    # Relationships
    employee = db.relationship("User", back_populates="attendance_records")

    def calculate_hours(self):
        """Auto-calculate working_hours when check_out is set."""
        if self.check_in and self.check_out:
            delta = self.check_out - self.check_in
            self.working_hours = round(delta.total_seconds() / 3600, 2)

    def get_status(self):
        """Calculate status dynamically based on check-in time."""
        if not self.check_in:
            return "Absent"
        import datetime as dt
        # Convert naive UTC datetime to Asia/Kolkata (IST)
        if self.check_in.tzinfo is None:
            utc_dt = self.check_in.replace(tzinfo=dt.timezone.utc)
        else:
            utc_dt = self.check_in
        kolkata_tz = dt.timezone(dt.timedelta(hours=5, minutes=30))
        local_time = utc_dt.astimezone(kolkata_tz).time()
        
        if local_time < dt.time(10, 0, 0):
            return "Present"
        elif local_time < dt.time(13, 0, 0):
            return "Half Day"
        else:
            return "Absent"

    def to_dict(self):
        return {
            "id": self.id,
            "employee_id": self.employee_id,
            "employee_name": self.employee.name if self.employee else None,
            "date": self.date.isoformat(),
            "check_in": (self.check_in.isoformat() + "Z") if self.check_in else None,
            "check_out": (self.check_out.isoformat() + "Z") if self.check_out else None,
            "working_hours": float(self.working_hours) if self.working_hours else 0.0,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "attendance_status": self.get_status()
        }


# ============================================================
# Meeting
# ============================================================
class Meeting(db.Model):
    __tablename__ = "meetings"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=True)
    department_id = db.Column(db.Integer, db.ForeignKey("departments.id"), nullable=True)  # NULL = company-wide
    scheduled_at = db.Column(db.DateTime, nullable=False)
    duration_minutes = db.Column(db.Integer, default=30)
    link = db.Column(db.String(255), nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    department = db.relationship("Department", back_populates="meetings")
    creator = db.relationship("User", foreign_keys=[created_by])

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "department_id": self.department_id,
            "department_name": self.department.name if self.department else "Company-Wide",
            "scheduled_at": self.scheduled_at.isoformat() + "Z",
            "duration_minutes": self.duration_minutes,
            "link": self.link,
            "created_by": self.created_by,
            "creator_name": self.creator.name if self.creator else None,
            "created_at": self.created_at.isoformat() + "Z",
        }


# ============================================================
# Task
# ============================================================
class Task(db.Model):
    __tablename__ = "tasks"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=True)
    employee_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    status = db.Column(db.Enum("Pending", "In Progress", "Completed"), default="Pending", index=True)
    due_date = db.Column(db.Date, nullable=True)
    assigned_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    employee = db.relationship("User", foreign_keys=[employee_id], back_populates="tasks")
    assigner = db.relationship("User", foreign_keys=[assigned_by])

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "employee_id": self.employee_id,
            "employee_name": self.employee.name if self.employee else None,
            "status": self.status,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "assigned_by": self.assigned_by,
            "assigner_name": self.assigner.name if self.assigner else None,
            "created_at": self.created_at.isoformat() + "Z",
        }


# ============================================================
# System Setting
# ============================================================
class SystemSetting(db.Model):
    __tablename__ = "system_settings"

    key = db.Column(db.String(100), primary_key=True)
    value = db.Column(db.String(255), nullable=False)

    @classmethod
    def get_value(cls, key, default=None, type_cast=str):
        try:
            setting = cls.query.filter_by(key=key).first()
            if setting:
                if type_cast == bool:
                    return setting.value.lower() == 'true'
                return type_cast(setting.value)
        except Exception:
            pass
        return default

    def to_dict(self):
        return {
            "key": self.key,
            "value": self.value,
        }


# ============================================================
# Attendance Adjustment / Regularization
# ============================================================
class AttendanceAdjustment(db.Model):
    __tablename__ = "attendance_adjustments"

    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    date = db.Column(db.Date, nullable=False)
    check_in = db.Column(db.DateTime, nullable=True)
    check_out = db.Column(db.DateTime, nullable=True)
    original_check_in = db.Column(db.DateTime, nullable=True)
    original_check_out = db.Column(db.DateTime, nullable=True)
    reason = db.Column(db.Text, nullable=False)
    status = db.Column(db.Enum("Pending", "Approved", "Rejected"), default="Pending", nullable=False)
    approval_comment = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    actioned_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    actioned_at = db.Column(db.DateTime, nullable=True)

    # Relationships
    employee = db.relationship("User", foreign_keys=[employee_id], backref=db.backref("adjustments", lazy="dynamic", cascade="all, delete-orphan"))
    actioned_by_user = db.relationship("User", foreign_keys=[actioned_by])

    def to_dict(self):
        return {
            "id": self.id,
            "employee_id": self.employee_id,
            "employee_name": self.employee.name if self.employee else None,
            "date": self.date.isoformat(),
            "check_in": (self.check_in.isoformat() + "Z") if self.check_in else None,
            "check_out": (self.check_out.isoformat() + "Z") if self.check_out else None,
            "original_check_in": (self.original_check_in.isoformat() + "Z") if self.original_check_in else None,
            "original_check_out": (self.original_check_out.isoformat() + "Z") if self.original_check_out else None,
            "reason": self.reason,
            "status": self.status,
            "approval_comment": self.approval_comment,
            "created_at": self.created_at.isoformat() + "Z",
            "actioned_by": self.actioned_by,
            "actioned_by_name": self.actioned_by_user.name if self.actioned_by_user else None,
            "actioned_at": (self.actioned_at.isoformat() + "Z") if self.actioned_at else None,
        }

# ============================================================
# Holiday
# ============================================================
class Holiday(db.Model):
    __tablename__ = "holidays"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    date = db.Column(db.Date, unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "date": self.date.isoformat(),
            "description": self.description,
            "created_at": self.created_at.isoformat() + "Z",
        }


# ============================================================
# Approval Request
# ============================================================
class ApprovalRequest(db.Model):
    __tablename__ = "approval_requests"
    __table_args__ = (
        db.Index("idx_approvals_approver_status", "approver_id", "status"),
        db.Index("idx_approvals_target", "module_type", "target_id"),
    )

    id = db.Column(db.Integer, primary_key=True)
    requester_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    approver_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    module_type = db.Column(db.String(50), nullable=False)
    target_id = db.Column(db.Integer, nullable=False)
    step_sequence = db.Column(db.Integer, default=1, nullable=False)
    status = db.Column(db.Enum("Pending", "Approved", "Rejected"), default="Pending", nullable=False)
    comments = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    actioned_at = db.Column(db.DateTime, nullable=True)

    # Relationships
    requester = db.relationship("User", foreign_keys=[requester_id], backref=db.backref("requested_approvals", lazy="dynamic"))
    approver = db.relationship("User", foreign_keys=[approver_id], backref=db.backref("assigned_approvals", lazy="dynamic"))

    def to_dict(self):
        # Dynamic import to avoid circular dependencies
        from models import UserProfileUpdate, WorkTransferRequest, CompOffRequest, ResumeUpdateRequest
        target_details = None
        if self.module_type == "UserProfileUpdate":
            target = UserProfileUpdate.query.get(self.target_id)
            if target:
                target_details = target.to_dict()
        elif self.module_type == "WorkTransfer":
            target = WorkTransferRequest.query.get(self.target_id)
            if target:
                target_details = target.to_dict()
        elif self.module_type == "CompOff":
            target = CompOffRequest.query.get(self.target_id)
            if target:
                target_details = target.to_dict()
        elif self.module_type == "ResumeUpdate":
            target = ResumeUpdateRequest.query.get(self.target_id)
            if target:
                target_details = target.to_dict()

        return {
            "id": self.id,
            "requester_id": self.requester_id,
            "requester_name": self.requester.name if self.requester else None,
            "approver_id": self.approver_id,
            "approver_name": self.approver.name if self.approver else None,
            "module_type": self.module_type,
            "target_id": self.target_id,
            "target_details": target_details,
            "step_sequence": self.step_sequence,
            "status": self.status,
            "comments": self.comments,
            "created_at": self.created_at.isoformat() + "Z",
            "actioned_at": (self.actioned_at.isoformat() + "Z") if self.actioned_at else None,
        }


# ============================================================
# Approval Log
# ============================================================
class ApprovalLog(db.Model):
    __tablename__ = "approval_logs"

    id = db.Column(db.Integer, primary_key=True)
    approval_request_id = db.Column(db.Integer, db.ForeignKey("approval_requests.id", ondelete="CASCADE"), nullable=False)
    actioner_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    old_status = db.Column(db.String(20), nullable=False)
    new_status = db.Column(db.String(20), nullable=False)
    comments = db.Column(db.Text, nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    request = db.relationship("ApprovalRequest", backref=db.backref("logs", lazy="dynamic", cascade="all, delete-orphan"))
    actioner = db.relationship("User", foreign_keys=[actioner_id])

    def to_dict(self):
        return {
            "id": self.id,
            "approval_request_id": self.approval_request_id,
            "actioner_id": self.actioner_id,
            "actioner_name": self.actioner.name if self.actioner else None,
            "old_status": self.old_status,
            "new_status": self.new_status,
            "comments": self.comments,
            "timestamp": self.timestamp.isoformat() + "Z",
        }


# ============================================================
# User Profile Update Request
# ============================================================
class UserProfileUpdate(db.Model):
    __tablename__ = "user_profile_updates"

    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    requested_changes = db.Column(db.JSON, nullable=False)
    original_values = db.Column(db.JSON, nullable=False)
    approval_request_id = db.Column(db.Integer, db.ForeignKey("approval_requests.id", ondelete="SET NULL"), nullable=True)
    status = db.Column(db.Enum("Pending", "Approved", "Rejected"), default="Pending", nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    employee = db.relationship("User", foreign_keys=[employee_id], backref=db.backref("profile_updates", lazy="dynamic", cascade="all, delete-orphan"))
    approval_request = db.relationship("ApprovalRequest", foreign_keys=[approval_request_id])

    def to_dict(self):
        return {
            "id": self.id,
            "employee_id": self.employee_id,
            "employee_name": self.employee.name if self.employee else None,
            "requested_changes": self.requested_changes,
            "original_values": self.original_values,
            "approval_request_id": self.approval_request_id,
            "status": self.status,
            "created_at": self.created_at.isoformat() + "Z",
            "updated_at": self.updated_at.isoformat() + "Z",
        }


# ============================================================
# Resume Update Request
# ============================================================
class ResumeUpdateRequest(db.Model):
    __tablename__ = "resume_update_requests"

    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    resume_url = db.Column(db.String(255), nullable=False)
    status = db.Column(db.Enum("Pending", "Approved", "Rejected"), default="Pending", nullable=False)
    approval_request_id = db.Column(db.Integer, db.ForeignKey("approval_requests.id", ondelete="SET NULL"), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    employee = db.relationship("User", foreign_keys=[employee_id])
    approval_request = db.relationship("ApprovalRequest", foreign_keys=[approval_request_id])

    def to_dict(self):
        return {
            "id": self.id,
            "employee_id": self.employee_id,
            "employee_name": self.employee.name if self.employee else None,
            "resume_url": self.resume_url,
            "status": self.status,
            "approval_request_id": self.approval_request_id,
            "created_at": self.created_at.isoformat() + "Z",
        }


# ============================================================
# Notification
# ============================================================
class Notification(db.Model):
    __tablename__ = "notifications"
    __table_args__ = (
        db.Index("idx_notifications_user_read", "user_id", "is_read"),
        db.Index("idx_notifications_user_created", "user_id", "created_at"),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False, nullable=False)
    notification_type = db.Column(db.String(50), nullable=False)
    target_id = db.Column(db.Integer, nullable=True)
    action_url = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    user = db.relationship("User", foreign_keys=[user_id], backref=db.backref("notifications", lazy="dynamic", cascade="all, delete-orphan"))

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "title": self.title,
            "content": self.content,
            "is_read": self.is_read,
            "notification_type": self.notification_type,
            "target_id": self.target_id,
            "action_url": self.action_url,
            "created_at": self.created_at.isoformat() + "Z",
        }


# ============================================================
# Announcement
# ============================================================
class Announcement(db.Model):
    __tablename__ = "announcements"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)
    audience_type = db.Column(db.Enum("All", "Department", "Employees", "Managers"), default="All", nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey("departments.id", ondelete="CASCADE"), nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    attachment_url = db.Column(db.String(255), nullable=True)

    # Relationships
    creator = db.relationship("User", foreign_keys=[created_by])
    department = db.relationship("Department", foreign_keys=[department_id])

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "audience_type": self.audience_type,
            "department_id": self.department_id,
            "department_name": self.department.name if self.department else None,
            "created_by": self.created_by,
            "creator_name": self.creator.name if self.creator else None,
            "created_at": self.created_at.isoformat() + "Z",
            "expires_at": self.expires_at.isoformat() + "Z" if self.expires_at else None,
            "is_active": self.is_active,
            "attachment_url": self.attachment_url,
        }


# ============================================================
# Work Transfer Request / Delegation
# ============================================================
class WorkTransferRequest(db.Model):
    __tablename__ = "work_transfer_requests"

    id = db.Column(db.Integer, primary_key=True)
    requester_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    delegate_to_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    transfer_tasks = db.Column(db.Boolean, default=False, nullable=False)
    transfer_approvals = db.Column(db.Boolean, default=False, nullable=False)
    transfer_meetings = db.Column(db.Boolean, default=False, nullable=False)
    status = db.Column(db.Enum("Pending", "Approved", "Rejected"), default="Pending", nullable=False)
    approval_request_id = db.Column(db.Integer, db.ForeignKey("approval_requests.id", ondelete="SET NULL"), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    requester = db.relationship("User", foreign_keys=[requester_id], backref=db.backref("sent_transfers", lazy="dynamic"))
    delegate = db.relationship("User", foreign_keys=[delegate_to_id], backref=db.backref("received_transfers", lazy="dynamic"))
    approval_request = db.relationship("ApprovalRequest", foreign_keys=[approval_request_id])

    def to_dict(self):
        return {
            "id": self.id,
            "requester_id": self.requester_id,
            "requester_name": self.requester.name if self.requester else None,
            "delegate_to_id": self.delegate_to_id,
            "delegate_name": self.delegate.name if self.delegate else None,
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat(),
            "transfer_tasks": self.transfer_tasks,
            "transfer_approvals": self.transfer_approvals,
            "transfer_meetings": self.transfer_meetings,
            "status": self.status,
            "approval_request_id": self.approval_request_id,
            "created_at": self.created_at.isoformat() + "Z",
        }


# ============================================================
# Registration Request
# ============================================================
class RegistrationRequest(db.Model):
    __tablename__ = "registration_requests"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    fathers_name = db.Column(db.String(100), nullable=True)
    dob = db.Column(db.Date, nullable=True)
    blood_group = db.Column(db.String(10), nullable=True)
    address = db.Column(db.Text, nullable=True)
    department_id = db.Column(db.Integer, db.ForeignKey("departments.id"), nullable=True)
    manager_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    status = db.Column(db.Enum("Pending", "Approved", "Rejected"), default="Pending", nullable=False)
    rejection_reason = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    actioned_at = db.Column(db.DateTime, nullable=True)

    department = db.relationship("Department", foreign_keys=[department_id])
    manager = db.relationship("User", foreign_keys=[manager_id])

    def to_dict(self):
        return {
            "id": self.id,
            "email": self.email,
            "name": self.name,
            "fathers_name": self.fathers_name,
            "dob": self.dob.isoformat() if self.dob else None,
            "blood_group": self.blood_group,
            "address": self.address,
            "department_id": self.department_id,
            "department_name": self.department.name if self.department else None,
            "manager_id": self.manager_id,
            "manager_name": self.manager.name if self.manager else None,
            "status": self.status,
            "rejection_reason": self.rejection_reason,
            "created_at": self.created_at.isoformat() + "Z",
            "actioned_at": (self.actioned_at.isoformat() + "Z") if self.actioned_at else None,
        }


# ============================================================
# Comp-Off Balance
# ============================================================
class CompOffBalance(db.Model):
    __tablename__ = "comp_off_balances"

    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    allocated = db.Column(db.Integer, default=0)
    used = db.Column(db.Integer, default=0)
    remaining = db.Column(db.Integer, default=0)

    employee = db.relationship("User", backref=db.backref("comp_off_balance", uselist=False, cascade="all, delete-orphan"))

    def recalculate(self):
        self.remaining = self.allocated - self.used

    def to_dict(self):
        return {
            "id": self.id,
            "employee_id": self.employee_id,
            "allocated": self.allocated,
            "used": self.used,
            "remaining": self.remaining
        }


# ============================================================
# Comp-Off Request
# ============================================================
class CompOffRequest(db.Model):
    __tablename__ = "comp_off_requests"

    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    date_worked = db.Column(db.Date, nullable=False)
    reason = db.Column(db.Text, nullable=False)
    status = db.Column(db.Enum("Pending", "Approved", "Rejected"), default="Pending", nullable=False)
    rejection_reason = db.Column(db.String(255), nullable=True)
    approval_request_id = db.Column(db.Integer, db.ForeignKey("approval_requests.id", ondelete="SET NULL"), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    actioned_at = db.Column(db.DateTime, nullable=True)

    employee = db.relationship("User", foreign_keys=[employee_id])
    approval_request = db.relationship("ApprovalRequest", foreign_keys=[approval_request_id])

    def to_dict(self):
        return {
            "id": self.id,
            "employee_id": self.employee_id,
            "employee_name": self.employee.name if self.employee else None,
            "date_worked": self.date_worked.isoformat(),
            "reason": self.reason,
            "status": self.status,
            "rejection_reason": self.rejection_reason,
            "approval_request_id": self.approval_request_id,
            "created_at": self.created_at.isoformat() + "Z",
            "actioned_at": (self.actioned_at.isoformat() + "Z") if self.actioned_at else None,
        }


# ============================================================
# Timesheet
# ============================================================
class Timesheet(db.Model):
    __tablename__ = "timesheets"

    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    date = db.Column(db.Date, nullable=False)
    task_name = db.Column(db.String(150), nullable=False)
    hours_spent = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.Enum("Submitted", "Approved", "Rejected"), default="Submitted", nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    employee = db.relationship("User", foreign_keys=[employee_id], backref=db.backref("timesheets", lazy="dynamic", cascade="all, delete-orphan"))

    def to_dict(self):
        return {
            "id": self.id,
            "employee_id": self.employee_id,
            "employee_name": self.employee.name if self.employee else None,
            "date": self.date.isoformat(),
            "task_name": self.task_name,
            "hours_spent": self.hours_spent,
            "description": self.description,
            "status": self.status,
            "created_at": self.created_at.isoformat() + "Z",
        }


# ============================================================
# Policy & Handbook (with Version History support)
# ============================================================
class Policy(db.Model):
    __tablename__ = "policies"

    id = db.Column(db.Integer, primary_key=True)
    policy_group_id = db.Column(db.Integer, nullable=True)
    version = db.Column(db.Integer, default=1, nullable=False)
    is_latest = db.Column(db.Boolean, default=True, nullable=False)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.Enum(
        "Leave Policy",
        "Attendance Policy",
        "WFH Policy",
        "Comp-Off Policy",
        "Code of Conduct",
        "Security Guidelines",
        "Employee Handbook"
    ), nullable=False)
    attachment_url = db.Column(db.String(255), nullable=True)
    updated_by = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    updater = db.relationship("User", foreign_keys=[updated_by])

    def to_dict(self):
        return {
            "id": self.id,
            "policy_group_id": self.policy_group_id,
            "version": self.version,
            "is_latest": self.is_latest,
            "title": self.title,
            "description": self.description,
            "category": self.category,
            "attachment_url": self.attachment_url,
            "updated_by": self.updated_by,
            "updated_by_name": self.updater.name if self.updater else "System",
            "updated_at": self.updated_at.isoformat() + "Z"
        }



