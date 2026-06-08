# HR Portal - User and Developer Guide

## Project Overview
This guide describes the user operations and developer setup for the HR Portal application, which tracks employee attendance, logs daily tasks, coordinates meetings, and processes leave requests.

## Problem Statement
Conventional HR operations face challenges with manual timekeeping and inaccurate check-ins. This application solves these issues by validating attendance using browser GPS location services.

## Key Features
*   Dual-mode dashboards for administrative and regular staff members.
*   Browser location capture to enforce check-in boundaries.
*   Interactive maps for administrative location configurations.
*   Leave quota visualization with progressive state displays.

## Tech Stack
*   **Client Engine:** React (v18.2.0), Axios, Recharts, Leaflet, React Router DOM
*   **Server Engine:** Flask, SQLAlchemy ORM, PyJWT, PyMySQL
*   **Database Engine:** MySQL Server (v8.x)

## System Architecture
The application runs on a decoupled client-server architecture:
*   **Frontend SPA Client:** Displays the user interfaces, queries endpoints, and renders Leaflet maps.
*   **Flask REST Backend:** Evaluates coordinates, queries databases, and handles route authorization.
*   **MySQL Database:** Normailized schemas storing activity history and user roles.

## Database Design
Operational schema mapping:
*   `user` - Store bio data, login credentials, and user permissions.
*   `attendance` - Track check-in/out timestamps and locations.
*   `leave_request` - Tracks employee leave types and statuses.
*   `system_settings` - Stores active coordinates.
*   `task` / `meeting` - Catalogs assigned duties and calendar schedules.

## User Roles
*   **Employee:** Dashboard views, geofenced check-in, leave application, and resume uploads.
*   **Admin:** Directory profiles inspection, account creation, leave approvals, task scheduling, and geofencing coordinates overrides.

## Authentication & Authorization
Security is enforced using JSON Web Tokens (JWT) inside HTTP headers. Administrative routes are protected using validation decorators.

## Attendance Management with Geofencing
Extracts high-accuracy coordinates and evaluates check-in eligibility by checking distance relative to the office using the Haversine equation.

## Leave Management
Enables staff members to apply for leave. Balance quotas update automatically upon approval.

## Task Management
Allows administrators to delegate assignments. Employees update task states.

## Meeting Management
Facilitates schedule logging. Meetings display on the user calendar grids.

## Profile & Resume Management
Allows employees to upload resumes. Sensitive profile data is restricted from colleague searches.

## Dashboard Analytics
Integrates Recharts area and bar widgets to track meeting density patterns and project tasks completion rates.

## OpenStreetMap Integration
Renders Leaflet map displays indicating office positions, user tracking markers, and check-in radius zones.

## Installation Guide
1. Import database: `CREATE DATABASE hr_portal;`
2. Install libraries: `pip install -r requirements.txt` and `npm install`
3. Database Setup: `python init_db.py`
4. Setup `.env` file with MySQL password and secret keys.
5. Launch API: `python app.py`
6. Launch client: `npm start`

## API Overview
*   `POST /api/auth/login` - Authenticate users.
*   `POST /api/attendance/checkin` - Submit attendance check-in.
*   `POST /api/attendance/settings` - Update office configuration.

## Screenshots Placeholders
*   **Analytics Grid:** `/screenshots/dashboard_analytics.png`
*   **Boundary Map:** `/screenshots/attendance_map_test.png`

## Contributors
Developer: Arpita
Course: B.Tech Computer Science & Engineering
