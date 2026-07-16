# HR Portal

[![Flask REST API](https://img.shields.io/badge/Backend-Flask-green.svg)](https://flask.palletsprojects.com/)
[![React Client](https://img.shields.io/badge/Frontend-React-blue.svg)](https://react.dev/)
[![MySQL Database](https://img.shields.io/badge/Database-MySQL-orange.svg)](https://www.mysql.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A state-of-the-art, professional enterprise Human Resource Management (HRM) platform built with a Flask REST API backend and a React frontend. The application automates workflows including geofenced attendance, leave processing, regularization requests, organization hierarchies, task tracking, and dynamic system configurations.

---

## Features

The HR Portal implements a comprehensive set of HRM capabilities:

- **JWT Authentication**: Secure user sessions using signed JSON Web Tokens passed in Authorization headers.
- **Role-Based Access Control (RBAC)**: Distinguishes permissions between **Admin**, **Line Manager**, and **Employee** roles.
- **Employee Management**: Comprehensive CRUD actions for directory profiles.
- **Employee Quick Profile Modal**: Clickable employee directory items that reveal detailed personal and employment cards inline.
- **Employee Directory**: Admin status filters (Active, Inactive, All) with greyed-out visual layouts for inactive staff.
- **Organization Hierarchy**: Tree visualization showing manager-subordinate relations.
- **Attendance Management**: Check-in and check-out tracking with statuses (Present, Late Arrival, Half Day, Absent).
- **Geofenced Attendance**: Validates check-ins using coordinate radius checking (Haversine equation) against office coordinates.
- **Attendance Regularization**: Allows employees to request correction of attendance records, which managers can approve or reject.
- **Leave Management**: Standard leave application, review, and approval cycles.
- **Annual Privilege Leave (APL)**: Tracks annual allocations and usages.
- **Work From Home (WFH)**: Applies flexible home-office quotas and limits.
- **Comp-Off Management**: Support for compensatory-off accrual and redemption.
- **Timesheet Management**: Weekly/monthly timesheet logging for project task management.
- **Task Management**: Delegation of work assignments from managers with real-time status updates (To Do, In Progress, Completed).
- **Meetings**: Create and join group calendars, notify attendees, and log agendas.
- **Announcements**: Broadcast system-wide updates and department announcements.
- **Resume Upload**: File upload and storage capabilities mapping resumes to employee database profiles.
- **Profile Management**: Profile picture uploads, password changes, and contact updates.
- **About Me / Bio**: Interactive section on the profile page allowing users to modify bios and summary parameters.
- **Email Notifications**: Automatic SMTP emails notifying managers on new leaves/regularizations and employees on decisions.
- **HR Analytics Dashboard**: Rich charts (using Recharts) analyzing department distribution, attendance metrics, and task statuses.
- **Department Management**: Logical separation of staff by departments (HR, Engineering, Sales, Marketing, etc.).
- **Self Registration & Approval Workflow**: Public registration endpoint where candidates request accounts, which admins can reject or approve.
- **Leave Balance Management**: Automates leave allocations and dynamically alters balances based on approvals.
- **Gender Support**: Tailors dynamic WFH limits based on employee gender.
- **Employee Soft Delete & Restore**: Deactivates login and hides employees from selection listings while leaving reporting hierarchies and historical logs intact.
- **Dynamic System Settings**: Admin configuration cards for Company, Leaves, Attendance, Security, and Notification limits.
- **Admin Self Profile Editing**: Restrictions prevent editing other admin accounts, but allow admins to modify their own profile.
- **Employee Detail Dashboard**: Custom views for employees to inspect their personal statistics.
- **CI/CD**: Continuous Integration and Deployment configurations powered by GitHub Actions.

---

## Screenshots

The following screenshot placeholders represent the core dashboards and modules of the system:

- **Login Page**: `docs/screenshots/login.png`
- **Analytics Dashboard**: `docs/screenshots/dashboard.png`
- **Employees Directory**: `docs/screenshots/employees.png`
- **Profile Management**: `docs/screenshots/profile.png`
- **Attendance Geofencing**: `docs/screenshots/attendance.png`
- **Leave Management**: `docs/screenshots/leaves.png`
- **Task Delegator**: `docs/screenshots/tasks.png`
- **System Settings Panel**: `docs/screenshots/settings.png`

---

## Tech Stack

| Tier | Technology | Description |
| :--- | :--- | :--- |
| **Frontend** | React (v18.2.0) | SPA layout and component engine |
| | React Router DOM (v6.x) | Declarative route management and navigation |
| | Axios | RESTful HTTP request client with interceptors |
| | Leaflet & React Leaflet | Interactive boundary maps and geofence coordinates |
| | Recharts | SVG charting library for interactive stats |
| **Backend** | Flask | Lightweight, scalable Python web framework |
| | SQLAlchemy ORM | SQL schema mapper and abstraction layer |
| | PyJWT | JSON Web Token encoding and signature verification |
| | PyMySQL | Pure-Python MySQL database driver |
| **Database** | MySQL Server (v8.x) | Relational database containing normalized tables |
| **Other** | OpenStreetMap | Map tile providers |
| | SMTP Email | Mail server protocol integration |
| | OpenPyXL | Excel spreadsheet exporter |
| | GitHub Actions | Automation workflows |

---

## Project Structure

```
HR-Portal Project/
├── .github/
│   └── workflows/
│       └── ci-cd.yml
├── backend/
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── announcements.py
│   │   ├── approvals.py
│   │   ├── attendance.py
│   │   ├── auth.py
│   │   ├── comp_off.py
│   │   ├── departments.py
│   │   ├── employees.py
│   │   ├── exports.py
│   │   ├── hierarchy.py
│   │   ├── holidays.py
│   │   ├── leaves.py
│   │   ├── meetings.py
│   │   ├── notifications.py
│   │   ├── policies.py
│   │   ├── profile.py
│   │   ├── registrations.py
│   │   ├── settings.py
│   │   ├── tasks.py
│   │   ├── team_dashboard.py
│   │   ├── timesheets.py
│   │   └── work_transfers.py
│   ├── uploads/
│   ├── utils/
│   │   └── decorators.py
│   ├── app.py
│   ├── config.py
│   ├── extensions.py
│   ├── init_db.py
│   ├── models.py
│   ├── requirements.txt
│   └── schema.sql
├── frontend/
│   ├── build/
│   ├── public/
│   └── src/
│       ├── components/
│       │   ├── common/
│       │   ├── forms/
│       │   └── layout/
│       ├── context/
│       │   └── AuthContext.js
│       ├── pages/
│       │   ├── AdminDashboard.js
│       │   ├── Announcements.js
│       │   ├── Approvals.js
│       │   ├── Attendance.js
│       │   ├── CompOff.js
│       │   ├── Dashboard.js
│       │   ├── Departments.js
│       │   ├── Directory.js
│       │   ├── EmployeeDashboard.js
│       │   ├── EmployeeDetailDashboard.js
│       │   ├── Employees.js
│       │   ├── Holidays.js
│       │   ├── Leaves.js
│       │   ├── Login.js
│       │   ├── Meetings.js
│       │   ├── Notifications.js
│       │   ├── OrgChart.js
│       │   ├── Policies.js
│       │   ├── Profile.js
│       │   ├── Register.js
│       │   ├── RegistrationRequests.js
│       │   ├── Settings.js
│       │   ├── Tasks.js
│       │   ├── TeamDashboard.js
│       │   ├── Timesheets.js
│       │   └── WorkTransfers.js
│       ├── services/
│       │   └── api.js
│       ├── App.js
│       ├── index.css
│       └── index.js
└── scratch/
    ├── verify_soft_delete_and_settings.py
    └── run_e2e_suite.py
```

---

## Database Design

The relational database contains the following normalized tables:

*   `departments`: Defines distinct organization business units.
*   `users`: Stores credentials, roles (Admin, Employee), and general details.
*   `leave_balances`: Tracks leave types (APL, WFH, etc.) allocated and used per employee.
*   `leaves`: Stores employee leave requests and their current workflow states.
*   `attendance`: Logs check-in/check-out times, status codes, and coordinate scopes.
*   `meetings`: Catalogs organizer links and attendee list definitions.
*   `tasks`: Manages task names, descriptions, assignees, and state records.
*   `system_settings`: Stores key-value items for configurations (APL limits, password rules, geofencing coordinates).
*   `attendance_adjustments`: Logs requested regularizations for check-in/out adjustments.
*   `holidays`: Catalog of general office holidays.
*   `approval_requests`: Tracks generic approval requests across leave/regularization modules.
*   `approval_logs`: Audit trail mapping status updates for request submissions.
*   `user_profile_updates`: Stores proposed changes from employees for Admin review.
*   `resume_update_requests`: Manages resume document verification requests.
*   `notifications`: Logs unread updates and alerts shown in the client badge.
*   `announcements`: Broadcasts active notice banners on dashboards.
*   `work_transfer_requests`: Maps responsibility delegation logs when employees take leave.
*   `registration_requests`: Logs candidate signup detail submissions awaiting Admin verification.
*   `comp_off_balances`: Tracks accrued compensatory balance quotas.
*   `comp_off_requests`: Tracks applications for comp-off leave conversions.
*   `timesheets`: Logs weekly project tasks and compliance hours.
*   `policies`: Stores file URLs and references for official HR policy booklets.

---

## Installation

### 1. Database Setup
Create a new MySQL database:
```sql
CREATE DATABASE hr_portal;
```

### 2. Backend Installation
Create a Python virtual environment and install dependencies:
```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

Run the database setup script to apply migrations and seed initial default system settings:
```bash
python init_db.py
```

### 3. Frontend Installation
Install npm dependencies in the frontend folder:
```bash
cd ../frontend
npm install
```

---

## Environment Variables

Copy the example file to a new `.env` file in the `backend/` directory:
```bash
cp backend/.env.example backend/.env
```

Define the following environment variables:

| Variable | Description | Default |
| :--- | :--- | :--- |
| `FLASK_ENV` | Mode of the server (`development` or `production`) | `development` |
| `SECRET_KEY` | Symmetric session encryption key | `change_me_to_a_long_random_secret_key` |
| `JWT_SECRET_KEY` | Signature key for JWT claims verification | `change_me_to_another_long_random_secret` |
| `DB_HOST` | Host address of the MySQL Server | `localhost` |
| `DB_USER` | MySQL Username | `root` |
| `DB_PASSWORD` | MySQL User Password | `your_mysql_password_here` |
| `DB_NAME` | Database schema name | `hr_portal` |
| `DB_PORT` | Port number of the database server | `3306` |
| `SMTP_HOST` | Host address of the outgoing mail SMTP server | `smtp.gmail.com` |
| `SMTP_PORT` | Outgoing port of the mail server | `587` |
| `SMTP_USER` | Authenticating SMTP account username | `your_email@gmail.com` |
| `SMTP_PASSWORD` | SMTP account application password | `your_app_password_here` |
| `SMTP_FROM` | Sender address appearing in notifications | `your_email@gmail.com` |
| `ADMIN_NOTIFY_EMAIL` | Target email for self-registration alerts | `admin@yourcompany.com` |
| `OFFICE_LATITUDE` | Fallback office center latitude | `28.6139` |
| `OFFICE_LONGITUDE` | Fallback office center longitude | `77.2090` |
| `OFFICE_RADIUS_METERS`| Fallback allowed radius for check-in | `200` |

---

## Running the Project

### Development Mode

Start the backend Flask API server:
```bash
cd backend
venv\Scripts\activate
flask run
```

Start the React development server:
```bash
cd frontend
npm start
```
The React app will proxy API calls to the local Flask server at `http://127.0.0.1:5000`.

### Production Mode

Compile the React frontend client:
```bash
cd frontend
npm run build
```

Run Flask through a production WSGI server (e.g. Waitress or Gunicorn):
```bash
cd ../backend
waitress-serve --port=5000 wsgi:app
```

---

## API Overview

The backend uses segmented API blueprints mapping to the following modules:

- **Auth (`/api/auth`)**: Coordinates user logins, token verification, and session timeouts.
- **Employees (`/api/employees`)**: Manages employee directory data, status filters, soft deletions, and restorations.
- **Approvals (`/api/approvals`)**: Handles leaves and attendance regularization approvals.
- **Attendance (`/api/attendance`)**: Stores attendance logs, processes coordinates, and manages regularizations.
- **Comp-Off (`/api/comp_off`)**: Handles compensatory off accruals and redemptions.
- **Departments (`/api/departments`)**: Returns available company departments for assignment.
- **Exports (`/api/exports`)**: Exporter formats generating XLSX spreadsheets for attendance and leave summaries.
- **Holidays (`/api/holidays`)**: Feeds active organization holiday calendars.
- **Leaves (`/api/leaves`)**: Manages leave balance allocations, request creation, and approvals.
- **Meetings (`/api/meetings`)**: Schedules group events, calendar invites, and organizer links.
- **Notifications (`/api/notifications`)**: Logs user notification list and unread badge status.
- **Policies (`/api/policies`)**: Manages official HR policy file uploads and downloads.
- **Profile (`/api/profile`)**: Updates user bio, experience summaries, and profiles.
- **Registrations (`/api/registrations`)**: Processes self-registration requests, validation limits, and admin approval workflows.
- **Settings (`/api/settings`)**: Manages system configurations dynamically in database key-value settings.
- **Announcements (`/api/announcements`)**: Publishes dashboard notices and notifications.
- **Team Dashboard (`/api/team_dashboard`)**: Summarizes analytics charts for manager teams.
- **Tasks (`/api/tasks`)**: Handles task creations, assignees, updates, and manager overrides.
- **Timesheets (`/api/timesheets`)**: Logs weekly project tasks and compliance hours.
- **Work Transfers (`/api/work_transfers`)**: Coordinates tasks transfers while employees are away.

---

## Security

- **JWT Authentication**: Expiring signature tokens prevent unauthorized page access.
- **Password Hashing**: Enforced using `bcrypt` salting and hashing.
- **Role-Based Authorization**: Route-level middleware (`@admin_required` and `@jwt_required`) protects endpoints.
- **Soft Delete**: Deactivates login without dropping historical foreign-key references.
- **Admin Protection**: Prevents modifications or password updates of other administrators.
- **Last Active Admin Safeguard**: Blocks self-deletion or directory deactivation of the last active administrator in the database.

---

## Business Rules

- **Employee IDs auto-generated when left blank**: Uses a default template based on department IDs if not manually defined.
- **Gender support**: Dynamic WFH quota limits tailored by gender parameters.
- **Default leave allocations**: System balances initialize dynamically using rules read from settings.
- **Leave balances may become negative**: Prevents workflow blocks when employees need extra leaves.
- **Soft delete preserves hierarchy**: `manager_id` references of subordinates remain untouched on manager deactivation.
- **Inactive employees cannot log in**: Displays visual status errors on login panels.
- **Only active employees appear in dropdowns**: Dropdown listings omit deactivated staff by default.
- **Admins can edit only their own Admin profile**: Blocks editing other admin credentials.
- **Last active Admin cannot be deleted**: Ensures system settings and configurations remain accessible.

---

## CI/CD

The repository includes a GitHub Actions configuration `.github/workflows/ci-cd.yml` which triggers automatically on pushes and pull requests to `main` and `master` branches:
- **Linting**: Runs `flake8` checks on python sources.
- **Backend Testing**: Runs unit tests via `pytest`.
- **Frontend Compilation**: Installs dependencies and runs `npm run build` to verify production builds.

---

## Future Enhancements

Potential roadmap extensions for the platform include:
- **Payroll**: Automated salary slip generation, tax deductions, and benefits management.
- **Performance Reviews**: Periodic appraisal dashboards and 360-degree feedback reviews.
- **Asset Management**: Tracking office laptop, desktop, and device allocations.
- **Mobile App**: Dedicated Android/iOS application with background location services.
- **Calendar Integration**: Google Calendar or Outlook Calendar sync for meetings and leaves.
- **Multi-factor Authentication (MFA)**: Enhancing login panels with authenticator app TOTP checks.

---

## License

This project is licensed under the [MIT License](LICENSE).

---

## Author

**Developed by Arpita Kundu**  
*Computer Science & Engineering*
