# backend/routes/policies.py
import os
from datetime import datetime
from flask import Blueprint, request, jsonify, current_app, send_from_directory
from werkzeug.utils import secure_filename
from extensions import db
from models import Policy, User
from utils.decorators import jwt_required, admin_required

policies_bp = Blueprint("policies", __name__)

ALLOWED_EXTENSIONS = {"pdf"}

def _allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def seed_default_policies():
    """Seeds the 9 default company policies if the table is empty."""
    admin = User.query.filter_by(role="Admin").first()
    admin_id = admin.id if admin else None

    default_policies = [
        {
            "title": "Leave Policy",
            "category": "Leave Policy",
            "description": (
                "### 1. Leave Entitlements\n"
                "- **Annual Privilege Leave (APL)**: Allocated at 20 days per calendar year.\n"
                "- **Work From Home (WFH)**:\n"
                "  - Female employees: 5 reference days per month.\n"
                "  - Male employees: 4 reference days per month.\n\n"
                "### 2. General Rules\n"
                "- **Negative Balances**: Leave balances are reference limits and may become negative if additional leaves are approved by managers.\n"
                "- **Prior Submission**: Employees are required to submit their leave requests in advance whenever possible.\n"
                "- **Emergency Leave**: In cases of emergencies, the leave must be immediately communicated to the reporting line manager."
            )
        },
        {
            "title": "Attendance Policy",
            "category": "Attendance Policy",
            "description": (
                "### 1. Daily Logs\n"
                "- Daily check-in and check-out are required for all working days.\n\n"
                "### 2. Validation & Regularization\n"
                "- **Geofenced Attendance**: Validation is enabled. Checks must occur within specified office boundaries.\n"
                "- **Missed Punches**: Attendance regularization requests are available for any missed punches.\n\n"
                "### 3. Compliance\n"
                "- Repeated attendance violations without regularization may trigger administrative review."
            )
        },
        {
            "title": "Work Hours Policy",
            "category": "Employee Handbook",
            "description": (
                "### 1. Working Hours\n"
                "- Standard working day is 9 hours (including break time).\n\n"
                "### 2. Responsibilities\n"
                "- Employees must successfully complete all assigned tasks and professional responsibilities.\n\n"
                "### 3. Compliance\n"
                "- Repeated lateness or failure to meet shift requirements may be reviewed by HR."
            )
        },
        {
            "title": "Code of Conduct",
            "category": "Code of Conduct",
            "description": (
                "### 1. Behavior\n"
                "- Professional workplace behavior is required at all times.\n\n"
                "### 2. Mutual Respect\n"
                "- Zero tolerance for harassment, discrimination, or abusive conduct of any form.\n\n"
                "### 3. Property Care\n"
                "- Respect colleagues and ensure proper care of company assets and property."
            )
        },
        {
            "title": "Information Security Policy",
            "category": "Security Guidelines",
            "description": (
                "### 1. Authentication\n"
                "- Under no circumstances should passwords or system credentials be shared.\n\n"
                "### 2. Confidentiality\n"
                "- Protect confidential company data, source code, and client information.\n\n"
                "### 3. Incident Reporting\n"
                "- Report any security incidents, breaches, or suspicious activity immediately to the IT team."
            )
        },
        {
            "title": "Remote Work Policy",
            "category": "WFH Policy",
            "description": (
                "### 1. Availability\n"
                "- Remote working employees must remain available during standard working hours.\n\n"
                "### 2. Workspace Requirements\n"
                "- A stable internet connection and quiet working environment are required.\n\n"
                "### 3. Managerial Requests\n"
                "- Reporting managers may request physical office presence when business requirements dictate."
            )
        },
        {
            "title": "IT Asset Policy",
            "category": "Employee Handbook",
            "description": (
                "### 1. Usage\n"
                "- All company-assigned IT assets and devices are for business use only.\n\n"
                "### 2. Care & Responsibility\n"
                "- Employees are fully responsible for the care and safety of their assigned equipment.\n\n"
                "### 3. Reporting\n"
                "- Any loss, theft, or physical damage must be reported within 24 hours."
            )
        },
        {
            "title": "Data Privacy Policy",
            "category": "Security Guidelines",
            "description": (
                "### 1. Confidentiality\n"
                "- Employee records, HR details, and company business records must remain confidential.\n\n"
                "### 2. Scoped Access\n"
                "- System and data access should be strictly limited to authorized personnel only."
            )
        },
        {
            "title": "Resignation & Exit Policy",
            "category": "Employee Handbook",
            "description": (
                "### 1. Resignation\n"
                "- A formal resignation process via email or portal is required.\n\n"
                "### 2. Clearance\n"
                "- All assigned company assets, equipment, and records must be returned before receiving exit clearance."
            )
        }
    ]

    for p in default_policies:
        policy = Policy(
            title=p["title"],
            description=p["description"],
            category=p["category"],
            updated_by=admin_id,
            version=1,
            is_latest=True
        )
        db.session.add(policy)
        db.session.flush()
        policy.policy_group_id = policy.id

    db.session.commit()

# ------------------------------------------------------------------
# GET /api/policies
# ------------------------------------------------------------------
@policies_bp.route("/", methods=["GET"])
@jwt_required
def get_policies(current_user_id, current_user_role):
    """Retrieve all latest active policies."""
    if Policy.query.count() == 0:
        try:
            seed_default_policies()
        except Exception:
            pass
    policies = Policy.query.filter_by(is_latest=True).order_by(Policy.category, Policy.title).all()
    return jsonify([p.to_dict() for p in policies]), 200

# ------------------------------------------------------------------
# GET /api/policies/stats
# ------------------------------------------------------------------
@policies_bp.route("/stats", methods=["GET"])
@jwt_required
def get_policies_stats(current_user_id, current_user_role):
    """Retrieve policy stats for the dashboard card."""
    total_policies = Policy.query.filter_by(is_latest=True).count()
    recently_updated = Policy.query.filter_by(is_latest=True).order_by(Policy.updated_at.desc()).limit(5).all()
    return jsonify({
        "total_policies": total_policies,
        "recently_updated": [p.to_dict() for p in recently_updated]
    }), 200

# ------------------------------------------------------------------
# GET /api/policies/<group_id>/history
# ------------------------------------------------------------------
@policies_bp.route("/<int:group_id>/history", methods=["GET"])
@jwt_required
def get_policy_history(group_id, current_user_id, current_user_role):
    """Retrieve all historical versions of a policy group."""
    versions = Policy.query.filter_by(policy_group_id=group_id).order_by(Policy.version.desc()).all()
    return jsonify([v.to_dict() for v in versions]), 200

# ------------------------------------------------------------------
# POST /api/policies
# ------------------------------------------------------------------
@policies_bp.route("/", methods=["POST"])
@jwt_required
@admin_required
def create_policy(current_user_id, current_user_role):
    """Admin only: Create a new policy (Version 1)."""
    title = request.form.get("title", "").strip()
    description = request.form.get("description", "").strip()
    category = request.form.get("category", "").strip()

    if not title or not description or not category:
        return jsonify({"error": "Title, description, and category are required."}), 400

    valid_categories = {
        "Leave Policy", "Attendance Policy", "WFH Policy", "Comp-Off Policy",
        "Code of Conduct", "Security Guidelines", "Employee Handbook"
    }
    if category not in valid_categories:
        return jsonify({"error": f"Invalid category. Must be one of: {', '.join(valid_categories)}"}), 400

    attachment_url = None
    if "attachment" in request.files:
        file = request.files["attachment"]
        if file.filename != "":
            if not _allowed_file(file.filename):
                return jsonify({"error": "Only PDF files are allowed for policies."}), 422
            
            # Save file
            filename = secure_filename(f"policy_{int(datetime.utcnow().timestamp())}_{file.filename}")
            upload_path = os.path.join(current_app.config["UPLOAD_FOLDER"], "policies")
            os.makedirs(upload_path, exist_ok=True)
            file.save(os.path.join(upload_path, filename))
            attachment_url = f"/api/policies/uploads/{filename}"

    # Create Policy
    policy = Policy(
        title=title,
        description=description,
        category=category,
        attachment_url=attachment_url,
        updated_by=current_user_id,
        version=1,
        is_latest=True
    )
    db.session.add(policy)
    db.session.commit()

    # Set policy_group_id to its own ID for first version
    policy.policy_group_id = policy.id
    db.session.commit()

    return jsonify(policy.to_dict()), 201

# ------------------------------------------------------------------
# PUT /api/policies/<int:policy_id>
# ------------------------------------------------------------------
@policies_bp.route("/<int:policy_id>", methods=["PUT"])
@jwt_required
@admin_required
def update_policy(policy_id, current_user_id, current_user_role):
    """Admin only: Edit a policy (creates a new version and deprecates the old one)."""
    current_policy = Policy.query.get(policy_id)
    if not current_policy:
        return jsonify({"error": "Policy not found."}), 404

    # Make sure we edit the latest version
    if not current_policy.is_latest:
        current_policy = Policy.query.filter_by(policy_group_id=current_policy.policy_group_id, is_latest=True).first()

    title = request.form.get("title", current_policy.title).strip()
    description = request.form.get("description", current_policy.description).strip()
    category = request.form.get("category", current_policy.category).strip()

    valid_categories = {
        "Leave Policy", "Attendance Policy", "WFH Policy", "Comp-Off Policy",
        "Code of Conduct", "Security Guidelines", "Employee Handbook"
    }
    if category not in valid_categories:
        return jsonify({"error": "Invalid category."}), 400

    attachment_url = current_policy.attachment_url
    if "attachment" in request.files:
        file = request.files["attachment"]
        if file.filename != "":
            if not _allowed_file(file.filename):
                return jsonify({"error": "Only PDF files are allowed for policies."}), 422
            
            # Save new file
            filename = secure_filename(f"policy_{int(datetime.utcnow().timestamp())}_{file.filename}")
            upload_path = os.path.join(current_app.config["UPLOAD_FOLDER"], "policies")
            os.makedirs(upload_path, exist_ok=True)
            file.save(os.path.join(upload_path, filename))
            attachment_url = f"/api/policies/uploads/{filename}"

    # Deprecate old latest version
    current_policy.is_latest = False
    
    # Create new version record
    new_policy = Policy(
        policy_group_id=current_policy.policy_group_id,
        version=current_policy.version + 1,
        is_latest=True,
        title=title,
        description=description,
        category=category,
        attachment_url=attachment_url,
        updated_by=current_user_id,
        updated_at=datetime.utcnow()
    )
    db.session.add(new_policy)
    db.session.commit()

    return jsonify(new_policy.to_dict()), 200

# ------------------------------------------------------------------
# DELETE /api/policies/<int:policy_id>
# ------------------------------------------------------------------
@policies_bp.route("/<int:policy_id>", methods=["DELETE"])
@jwt_required
@admin_required
def delete_policy(policy_id, current_user_id, current_user_role):
    """Admin only: Delete a policy group (deletes all versions)."""
    policy = Policy.query.get(policy_id)
    if not policy:
        return jsonify({"error": "Policy not found."}), 404

    # Delete all versions associated with this policy_group_id
    Policy.query.filter_by(policy_group_id=policy.policy_group_id).delete()
    db.session.commit()

    return jsonify({"message": "Policy deleted successfully."}), 200

# ------------------------------------------------------------------
# GET /api/policies/uploads/<path:filename>
# ------------------------------------------------------------------
@policies_bp.route("/uploads/<path:filename>", methods=["GET"])
def get_policy_upload(filename):
    """Public route: Retrieve uploaded policy files."""
    upload_path = os.path.join(current_app.config["UPLOAD_FOLDER"], "policies")
    return send_from_directory(upload_path, filename)
