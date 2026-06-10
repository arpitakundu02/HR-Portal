"""
backend/utils/email_service.py
-------------------------------
Asynchronous email notification service using SMTP and background threads.
Provides templates for leaves, employees, tasks, meetings, and resumes.
"""

import smtplib
import logging
import threading
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import current_app

logger = logging.getLogger(__name__)

# Base HTML Template wrapper
HTML_TEMPLATE_WRAPPER = """
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>HR Portal Notification</title>
</head>
<body style="margin: 0; padding: 0; background-color: #f3f4f6; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;">
  <table align="center" border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width: 600px; margin: 20px auto; background-color: #ffffff; border-radius: 8px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06); overflow: hidden; border: 1px solid #e5e7eb;">
    <!-- Header -->
    <tr>
      <td bgcolor="#4f46e5" style="padding: 24px 32px; text-align: center;">
        <span style="font-size: 24px; font-weight: 800; color: #ffffff; letter-spacing: 0.5px;">🏢 HR PORTAL</span>
      </td>
    </tr>
    <!-- Content Body -->
    <tr>
      <td style="padding: 32px 32px; color: #374151; line-height: 1.6;">
        {content}
      </td>
    </tr>
    <!-- Footer -->
    <tr>
      <td bgcolor="#f9fafb" style="padding: 20px 32px; text-align: center; font-size: 12px; color: #9ca3af; border-top: 1px solid #f3f4f6;">
        <p style="margin: 0 0 4px 0;">This is an automated system notification from the HR Portal.</p>
        <p style="margin: 0;">&copy; 2026 Enterprise HR Management System. All rights reserved.</p>
      </td>
    </tr>
  </table>
</body>
</html>
"""


def _build_message(to_email: str, subject: str, html_body: str) -> MIMEMultipart:
    """Build a MIME email message."""
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = current_app.config["SMTP_FROM"]
    msg["To"] = to_email
    msg.attach(MIMEText(html_body, "html"))
    return msg


def send_email(subject: str, body: str, recipient: str) -> bool:
    """
    Send an HTML email via SMTP with structured logging and retry logic.
    In development, if SMTP_USER is not configured, logs the email content instead (dev mode).
    This function blocks; use send_email_async for non-blocking.
    """
    import time
    from datetime import datetime

    timestamp = datetime.utcnow().isoformat() + " UTC"
    
    # Fallback to check app context config if not running in thread
    smtp_user = current_app.config.get("SMTP_USER", "")
    smtp_password = current_app.config.get("SMTP_PASSWORD", "")
    smtp_host = current_app.config.get("SMTP_HOST", "smtp.gmail.com")
    smtp_port = current_app.config.get("SMTP_PORT", 587)
    smtp_from = current_app.config.get("SMTP_FROM", "noreply@hrportal.com")

    # If body is not HTML wrapped, wrap it
    if "<html>" not in body:
        formatted_content = f"<p style='font-size: 16px; margin: 0;'>{body.replace(chr(10), '<br>')}</p>"
        html_body = HTML_TEMPLATE_WRAPPER.format(content=formatted_content)
    else:
        html_body = body

    if not smtp_user:
        logger.info(
            "[EMAIL - DEV/CONSOLE MODE] [SUCCESS] [Timestamp: %s] To: %s | Subject: %s\n%s",
            timestamp, recipient, subject, html_body
        )
        # Also print to stdout for simple logs verification
        print(f"\n[STDOUT EMAIL] [SUCCESS] [Timestamp: {timestamp}] To: {recipient} | Subject: {subject}\n{body}\n")
        return True

    msg = _build_message(recipient, subject, html_body)
    max_retries = 3
    retry_delay = 2  # initial backoff in seconds

    for attempt in range(1, max_retries + 1):
        try:
            logger.info(
                "[EMAIL - SEND ATTEMPT %d/%d] [Timestamp: %s] To: %s | Subject: %s",
                attempt, max_retries, datetime.utcnow().isoformat() + " UTC", recipient, subject
            )
            with smtplib.SMTP(smtp_host, smtp_port, timeout=10) as server:
                server.ehlo()
                server.starttls()
                server.login(smtp_user, smtp_password)
                server.sendmail(smtp_from, recipient, msg.as_string())
            
            logger.info(
                "[EMAIL - SEND SUCCESS] [Timestamp: %s] To: %s | Subject: %s",
                datetime.utcnow().isoformat() + " UTC", recipient, subject
            )
            return True
        except (smtplib.SMTPConnectError, smtplib.SMTPServerDisconnected, smtplib.SMTPResponseException, OSError) as exc:
            logger.warning(
                "[EMAIL - RETRIABLE FAILURE] [Attempt %d/%d] [Timestamp: %s] To: %s | Error: %s",
                attempt, max_retries, datetime.utcnow().isoformat() + " UTC", recipient, str(exc)
            )
            if attempt < max_retries:
                time.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
            else:
                logger.error(
                    "[EMAIL - SEND FAILURE] [Final Attempt] [Timestamp: %s] To: %s | Subject: %s | Error: %s",
                    datetime.utcnow().isoformat() + " UTC", recipient, subject, str(exc)
                )
        except Exception as exc:
            logger.error(
                "[EMAIL - SEND FAILURE] [Non-retriable Error] [Timestamp: %s] To: %s | Subject: %s | Error: %s",
                datetime.utcnow().isoformat() + " UTC", recipient, subject, str(exc)
            )
            return False

    return False


def send_email_async(subject: str, body: str, recipient: str):
    """Run send_email in a background thread to prevent blocking the Flask app context."""
    # Capture current config values to pass to thread
    app_context_config = {
        "SMTP_HOST": current_app.config.get("SMTP_HOST"),
        "SMTP_PORT": current_app.config.get("SMTP_PORT"),
        "SMTP_USER": current_app.config.get("SMTP_USER"),
        "SMTP_PASSWORD": current_app.config.get("SMTP_PASSWORD"),
        "SMTP_FROM": current_app.config.get("SMTP_FROM")
    }

    def thread_target(subject, body, recipient, config):
        # Create a mock/temp flask app-like structure or pass config values inside thread
        try:
            # We construct a thread-safe send with explicit parameters
            # To ensure config values are accessible inside send_email, we temporarily bind them or run in app_context
            from app import create_app
            app = create_app()
            with app.app_context():
                send_email(subject, body, recipient)
        except Exception as err:
            logger.error("Thread failed to process send_email: %s", err)

    thread = threading.Thread(target=thread_target, args=(subject, body, recipient, app_context_config))
    thread.start()
    return thread


# ------------------------------------------------------------------ #
# Specific Notification Service Triggers
# ------------------------------------------------------------------ #

def send_leave_notification(employee_name: str, employee_id: str, leave_type: str,
                            start_date: str, end_date: str, reason: str,
                            recipient: str, status: str = None, comment: str = None) -> bool:
    """Send leave request submission (to Admin) or action update (to Employee) notifications."""
    if status is None:
        # Submission alert to Admin
        subject = "New Leave Request Submitted"
        content = f"""
        <h3 style="color: #4f46e5; margin-top: 0;">New Leave Application</h3>
        <p>A new leave request requires your administrative attention.</p>
        <hr style="border: 0; border-top: 1px solid #e5e7eb; margin: 16px 0;">
        <table style="width: 100%; font-size: 14px; border-collapse: collapse;">
          <tr><td style="padding: 6px 0; color: #6b7280; font-weight: 600;">Employee Name:</td><td style="padding: 6px 0; font-weight: 600;">{employee_name}</td></tr>
          <tr><td style="padding: 6px 0; color: #6b7280; font-weight: 600;">Employee ID:</td><td style="padding: 6px 0;">{employee_id}</td></tr>
          <tr><td style="padding: 6px 0; color: #6b7280; font-weight: 600;">Leave Type:</td><td style="padding: 6px 0;">{leave_type}</td></tr>
          <tr><td style="padding: 6px 0; color: #6b7280; font-weight: 600;">Start Date:</td><td style="padding: 6px 0;">{start_date}</td></tr>
          <tr><td style="padding: 6px 0; color: #6b7280; font-weight: 600;">End Date:</td><td style="padding: 6px 0;">{end_date}</td></tr>
          <tr><td style="padding: 6px 0; color: #6b7280; font-weight: 600;">Reason:</td><td style="padding: 6px 0; color: #4b5563;">{reason or "No reason provided"}</td></tr>
        </table>
        """
    else:
        # Action update to Employee
        subject = "Leave Request Updated"
        color = "#10b981" if status == "Approved" else "#ef4444"
        content = f"""
        <h3 style="color: {color}; margin-top: 0;">Leave Request {status}</h3>
        <p>Your leave request status has been updated by the Admin.</p>
        <hr style="border: 0; border-top: 1px solid #e5e7eb; margin: 16px 0;">
        <table style="width: 100%; font-size: 14px; border-collapse: collapse;">
          <tr><td style="padding: 6px 0; color: #6b7280; font-weight: 600;">Leave Type:</td><td style="padding: 6px 0; font-weight: 600;">{leave_type}</td></tr>
          <tr><td style="padding: 6px 0; color: #6b7280; font-weight: 600;">Duration:</td><td style="padding: 6px 0;">{start_date} to {end_date}</td></tr>
          <tr><td style="padding: 6px 0; color: #6b7280; font-weight: 600;">Leave Status:</td><td style="padding: 6px 0; color: {color}; font-weight: 700;">{status}</td></tr>
          {f"<tr><td style='padding: 6px 0; color: #6b7280; font-weight: 600;'>Comments:</td><td style='padding: 6px 0; color: #4b5563;'>{comment}</td></tr>" if comment else ""}
        </table>
        """
    body = HTML_TEMPLATE_WRAPPER.format(content=content)
    send_email_async(subject, body, recipient)
    return True


def send_employee_notification(employee_id: str, email: str, temp_password: str,
                               portal_url: str, recipient: str, employee_name: str) -> bool:
    """Send welcome onboarding credentials email to newly created employees."""
    subject = "Employee Onboarding Details"
    content = f"""
    <h3 style="color: #4f46e5; margin-top: 0;">Welcome to the Team, {employee_name}!</h3>
    <p>Your employee account has been created by the Human Resources administrator.</p>
    <p>Please use the following login credentials to access the Portal:</p>
    <hr style="border: 0; border-top: 1px solid #e5e7eb; margin: 16px 0;">
    <table style="width: 100%; font-size: 14px; border-collapse: collapse;">
      <tr><td style="padding: 6px 0; color: #6b7280; font-weight: 600;">Employee ID:</td><td style="padding: 6px 0; font-weight: 600;">{employee_id}</td></tr>
      <tr><td style="padding: 6px 0; color: #6b7280; font-weight: 600;">Login Email:</td><td style="padding: 6px 0;">{email}</td></tr>
      <tr><td style="padding: 6px 0; color: #6b7280; font-weight: 600;">Temporary Password:</td><td style="padding: 6px 0; font-family: monospace; font-size: 15px; color: #b45309; font-weight: bold;">{temp_password}</td></tr>
      <tr><td style="padding: 6px 0; color: #6b7280; font-weight: 600;">Portal URL:</td><td style="padding: 6px 0;"><a href="{portal_url}" style="color: #4f46e5; font-weight: 600;">{portal_url}</a></td></tr>
    </table>
    <p style="margin-top: 20px; font-size: 13px; color: #6b7280; background: #fffbeb; border: 1px solid #fef3c7; padding: 10px; border-radius: 4px;">
      ⚠️ <strong>Security Note:</strong> Please change your temporary password immediately upon logging in for the first time.
    </p>
    """
    body = HTML_TEMPLATE_WRAPPER.format(content=content)
    send_email_async(subject, body, recipient)
    return True


def send_task_notification(task_name: str, description: str, priority: str,
                           due_date: str, recipient: str, employee_name: str = None,
                           is_completed: bool = False) -> bool:
    """Send task assignment alerts to employees or completion updates to Admins."""
    if not is_completed:
        subject = "New Task Assigned"
        content = f"""
        <h3 style="color: #4f46e5; margin-top: 0;">Task Assigned</h3>
        <p>A new task has been assigned to you. Details are outlined below:</p>
        <hr style="border: 0; border-top: 1px solid #e5e7eb; margin: 16px 0;">
        <table style="width: 100%; font-size: 14px; border-collapse: collapse;">
          <tr><td style="padding: 6px 0; color: #6b7280; font-weight: 600;">Task Name:</td><td style="padding: 6px 0; font-weight: 600;">{task_name}</td></tr>
          <tr><td style="padding: 6px 0; color: #6b7280; font-weight: 600;">Description:</td><td style="padding: 6px 0; color: #4b5563;">{description or "No description provided"}</td></tr>
          <tr><td style="padding: 6px 0; color: #6b7280; font-weight: 600;">Priority:</td><td style="padding: 6px 0;"><span style="background: #fee2e2; color: #991b1b; padding: 2px 6px; border-radius: 4px; font-size: 12px; font-weight: 600;">{priority or "Normal"}</span></td></tr>
          <tr><td style="padding: 6px 0; color: #6b7280; font-weight: 600;">Due Date:</td><td style="padding: 6px 0; font-weight: 600; color: #b91c1c;">{due_date or "No due date"}</td></tr>
        </table>
        """
    else:
        subject = "Task Completed"
        content = f"""
        <h3 style="color: #10b981; margin-top: 0;">Task Marked Complete</h3>
        <p>Employee <strong>{employee_name}</strong> has completed their assigned task.</p>
        <hr style="border: 0; border-top: 1px solid #e5e7eb; margin: 16px 0;">
        <table style="width: 100%; font-size: 14px; border-collapse: collapse;">
          <tr><td style="padding: 6px 0; color: #6b7280; font-weight: 600;">Task Name:</td><td style="padding: 6px 0; font-weight: 600;">{task_name}</td></tr>
          <tr><td style="padding: 6px 0; color: #6b7280; font-weight: 600;">Description:</td><td style="padding: 6px 0; color: #4b5563;">{description or "—"}</td></tr>
          <tr><td style="padding: 6px 0; color: #6b7280; font-weight: 600;">Completed By:</td><td style="padding: 6px 0; font-weight: 600;">{employee_name}</td></tr>
        </table>
        """
    body = HTML_TEMPLATE_WRAPPER.format(content=content)
    send_email_async(subject, body, recipient)
    return True


def send_meeting_notification(meeting_title: str, date_str: str, time_str: str,
                              department_name: str, description: str, recipients: list) -> bool:
    """Send upcoming scheduled meeting details to a list of target recipients."""
    subject = "New Meeting Scheduled"
    content = f"""
    <h3 style="color: #4f46e5; margin-top: 0;">New Meeting Invitation</h3>
    <p>You have been scheduled for an upcoming corporate meeting.</p>
    <hr style="border: 0; border-top: 1px solid #e5e7eb; margin: 16px 0;">
    <table style="width: 100%; font-size: 14px; border-collapse: collapse;">
      <tr><td style="padding: 6px 0; color: #6b7280; font-weight: 600;">Meeting Title:</td><td style="padding: 6px 0; font-weight: 600;">{meeting_title}</td></tr>
      <tr><td style="padding: 6px 0; color: #6b7280; font-weight: 600;">Date & Time:</td><td style="padding: 6px 0; font-weight: 600; color: #1e3a8a;">{date_str} at {time_str}</td></tr>
      <tr><td style="padding: 6px 0; color: #6b7280; font-weight: 600;">Department:</td><td style="padding: 6px 0;">{department_name or "Company-Wide"}</td></tr>
      <tr><td style="padding: 6px 0; color: #6b7280; font-weight: 600;">Description:</td><td style="padding: 6px 0; color: #4b5563;">{description or "No agenda details provided."}</td></tr>
    </table>
    """
    body = HTML_TEMPLATE_WRAPPER.format(content=content)
    for email in recipients:
        if email:
            send_email_async(subject, body, email)
    return True


def send_resume_notification(employee_name: str, employee_id: str, upload_timestamp: str, recipient: str) -> bool:
    """Notify admin whenever an employee uploads or replaces their resume file."""
    subject = "Employee Resume File Upload Alert"
    content = f"""
    <h3 style="color: #4f46e5; margin-top: 0;">Resume Upload Alert</h3>
    <p>An employee has uploaded or updated their resume file in the system.</p>
    <hr style="border: 0; border-top: 1px solid #e5e7eb; margin: 16px 0;">
    <table style="width: 100%; font-size: 14px; border-collapse: collapse;">
      <tr><td style="padding: 6px 0; color: #6b7280; font-weight: 600;">Employee Name:</td><td style="padding: 6px 0; font-weight: 600;">{employee_name}</td></tr>
      <tr><td style="padding: 6px 0; color: #6b7280; font-weight: 600;">Employee ID:</td><td style="padding: 6px 0;">{employee_id}</td></tr>
      <tr><td style="padding: 6px 0; color: #6b7280; font-weight: 600;">Timestamp:</td><td style="padding: 6px 0;">{upload_timestamp}</td></tr>
    </table>
    <p style="margin-top: 20px;">Please login to the Admin Dashboard under the Employee Management section to view or download the resume.</p>
    """
    body = HTML_TEMPLATE_WRAPPER.format(content=content)
    send_email_async(subject, body, recipient)
    return True


def send_login_notification(email: str, recipient: str, name: str) -> bool:
    """Send login confirmation alert to the account owner."""
    subject = "HR Portal - Successful Login Notification"
    from datetime import datetime
    timestamp = datetime.utcnow().isoformat() + " UTC"
    content = f"""
    <h3 style="color: #4f46e5; margin-top: 0;">Successful Login Alert</h3>
    <p>Hello {name},</p>
    <p>Your HR Portal account has been successfully logged into.</p>
    <hr style="border: 0; border-top: 1px solid #e5e7eb; margin: 16px 0;">
    <table style="width: 100%; font-size: 14px; border-collapse: collapse;">
      <tr><td style="padding: 6px 0; color: #6b7280; font-weight: 600;">Account Email:</td><td style="padding: 6px 0;">{email}</td></tr>
      <tr><td style="padding: 6px 0; color: #6b7280; font-weight: 600;">Timestamp:</td><td style="padding: 6px 0;">{timestamp}</td></tr>
    </table>
    <p style="margin-top: 20px; font-size: 12px; color: #6b7280;">If this activity was not performed by you, please immediately reset your password or contact the system administrator.</p>
    """
    body = HTML_TEMPLATE_WRAPPER.format(content=content)
    send_email_async(subject, body, recipient)
    return True


def send_resume_confirmation(employee_name: str, employee_id: str, upload_timestamp: str, recipient: str) -> bool:
    """Send resume upload confirmation to the employee."""
    subject = "Resume Upload Confirmation"
    content = f"""
    <h3 style="color: #10b981; margin-top: 0;">Resume Uploaded Successfully</h3>
    <p>Hello {employee_name},</p>
    <p>This email confirms that your resume file has been successfully uploaded/updated in the HR Portal.</p>
    <hr style="border: 0; border-top: 1px solid #e5e7eb; margin: 16px 0;">
    <table style="width: 100%; font-size: 14px; border-collapse: collapse;">
      <tr><td style="padding: 6px 0; color: #6b7280; font-weight: 600;">Employee Name:</td><td style="padding: 6px 0; font-weight: 600;">{employee_name}</td></tr>
      <tr><td style="padding: 6px 0; color: #6b7280; font-weight: 600;">Employee ID:</td><td style="padding: 6px 0;">{employee_id}</td></tr>
      <tr><td style="padding: 6px 0; color: #6b7280; font-weight: 600;">Upload Time:</td><td style="padding: 6px 0;">{upload_timestamp}</td></tr>
    </table>
    <p style="margin-top: 20px;">You can view and update your resume anytime from your Profile page.</p>
    """
    body = HTML_TEMPLATE_WRAPPER.format(content=content)
    send_email_async(subject, body, recipient)
    return True


def send_regularization_notification(employee_name: str, employee_id: str, date_str: str,
                                     check_in_str: str, check_out_str: str, reason: str,
                                     recipient: str, status: str = None, comment: str = None) -> bool:
    """Send attendance regularization submission (to Admin) or action update (to Employee) notifications."""
    if status is None:
        # Submission alert to Admin
        subject = "New Attendance Regularization Request"
        content = f"""
        <h3 style="color: #4f46e5; margin-top: 0;">Attendance Regularization Submitted</h3>
        <p>A new attendance regularization request requires your administrative attention.</p>
        <hr style="border: 0; border-top: 1px solid #e5e7eb; margin: 16px 0;">
        <table style="width: 100%; font-size: 14px; border-collapse: collapse;">
          <tr><td style="padding: 6px 0; color: #6b7280; font-weight: 600;">Employee Name:</td><td style="padding: 6px 0; font-weight: 600;">{employee_name}</td></tr>
          <tr><td style="padding: 6px 0; color: #6b7280; font-weight: 600;">Employee ID:</td><td style="padding: 6px 0;">{employee_id}</td></tr>
          <tr><td style="padding: 6px 0; color: #6b7280; font-weight: 600;">Date:</td><td style="padding: 6px 0;">{date_str}</td></tr>
          <tr><td style="padding: 6px 0; color: #6b7280; font-weight: 600;">Requested Check-In:</td><td style="padding: 6px 0;">{check_in_str or "—"}</td></tr>
          <tr><td style="padding: 6px 0; color: #6b7280; font-weight: 600;">Requested Check-Out:</td><td style="padding: 6px 0;">{check_out_str or "—"}</td></tr>
          <tr><td style="padding: 6px 0; color: #6b7280; font-weight: 600;">Reason:</td><td style="padding: 6px 0; color: #4b5563;">{reason}</td></tr>
        </table>
        """
    else:
        # Action update to Employee
        subject = f"Attendance Regularization Request {status}"
        color = "#10b981" if status == "Approved" else "#ef4444"
        content = f"""
        <h3 style="color: {color}; margin-top: 0;">Regularization Request {status}</h3>
        <p>Your attendance regularization request status has been updated by the Admin.</p>
        <hr style="border: 0; border-top: 1px solid #e5e7eb; margin: 16px 0;">
        <table style="width: 100%; font-size: 14px; border-collapse: collapse;">
          <tr><td style="padding: 6px 0; color: #6b7280; font-weight: 600;">Date:</td><td style="padding: 6px 0; font-weight: 600;">{date_str}</td></tr>
          <tr><td style="padding: 6px 0; color: #6b7280; font-weight: 600;">Status:</td><td style="padding: 6px 0; color: {color}; font-weight: 700;">{status}</td></tr>
          {f"<tr><td style='padding: 6px 0; color: #6b7280; font-weight: 600;'>Admin Comment:</td><td style='padding: 6px 0; color: #4b5563;'>{comment}</td></tr>" if comment else ""}
        </table>
        """
    body = HTML_TEMPLATE_WRAPPER.format(content=content)
    send_email_async(subject, body, recipient)
    return True

