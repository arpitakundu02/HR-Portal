# Design and Evaluation of a Geolocated HR Portal

## 1. Abstract
This project details the creation of a secure HR Portal Management System. Incorporating geofenced attendance logs, role-based workflows, and data security measures, the system automates corporate human resource operations.

## 2. Introduction
Automating workforce management is essential for modern organizational efficiency. This system provides a digital suite replacing paper-based attendance logging with geolocated clock-ins, alongside leave tracking and task coordination features.

## 3. Objectives
*   Develop software-based location check-ins.
*   Integrate interactive visual maps for location diagnostics.
*   Enforce role-based access limits.
*   Ensure data confidentiality for employee records.

## 4. Scope
The scope consists of:
*   A React frontend utilizing CSS variables.
*   A Flask REST API backend executing authorization checks.
*   A MySQL database storing transactional records.
*   Diagnostics visualization using Leaflet.

## 5. System Requirements
*   **Hardware:** 8 GB RAM, Core i5 Processor, 500 MB disk space.
*   **Software:** Windows/macOS/Linux, MySQL 8, Node.js v16+, Python 3.10+.

## 6. Methodology
The development followed an Agile Software Development Life Cycle:
1.  **Analysis:** Researched geofence offsets and boundary metrics.
2.  **Schema Design:** Configured relational databases.
3.  **Client-Server Dev:** Decoupled frontend components and backend blueprints.
4.  **Testing:** Executed geolocation and endpoint privilege checks.

## 7. Modules Implemented
*   **Authentication Module:** Secure JWT token processing.
*   **Geofence Module:** Distance comparisons using the Haversine equation.
*   **Leave Module:** Quota indicators displaying progress details.
*   **Operations Module:** Task boards and meeting Density charts.

## 8. Database Design
The MySQL database is composed of:
*   `user` - Personal bio details, credentials, and user roles.
*   `attendance` - Clock-in and clock-out coordinates and timestamps.
*   `leave_request` - Vacation requests and quota balance values.
*   `system_settings` - Persistent office coordinates.

## 9. Security Measures
*   **Endpoint Guards:** Enforced via Flask decorators.
*   **Data Masking:** Profile listings strip sensitive details for peer queries.
*   **Access Check:** Verifies ID payloads to restrict resume downloads.

## 10. Testing & Verification
Tested geodesic distance checks:
```python
--- Current Settings ---
office_latitude: 28.390583
office_longitude: 77.064722
User: 28.39603879804401, 77.02748211222493
Calculated Distance: 3692.93 meters
Within 200m? False (Blocked as expected)
```

Verified permission boundaries:
*   Directory profile checks successfully strip sensitive information fields.
*   Resume file directories return HTTP 403 blocks for unauthorized requests.

## 11. Results
The portal compiles and executes correctly. Attendance parameters, leave balances, and map visualization components function dynamically.
*   **Dashboard view screenshot:** `/screenshots/dashboard_analytics.png`
*   **Boundary Map screenshot:** `/screenshots/attendance_map_test.png`

## 12. Challenges Faced
1.  **Sensor Deviation:** Handled user coordinates discrepancies using the Admin Map settings panel.
2.  **Missing Assets:** Built custom inline SVG markers in Leaflet to bypass file errors.

## 13. Future Scope
*   Dynamic geofence radius mappings.
*   IP location backup overrides.
*   Automated email indicators.

## 14. Conclusion
The HR Portal Management System securely tracks attendance and leave metrics. Decoupled configurations combined with Leaflet and OpenStreetMap visualizers deliver a solid framework for business operations.

## 15. Contributors
Developer: Arpita
Course: B.Tech Computer Science & Engineering
