This folder stores uploaded employee resume files.
Files are saved by the Flask backend when an Admin uploads a resume via:
  POST /api/employees/<id>/resume

Files are served (authenticated) via:
  GET /api/employees/uploads/<filename>

Supported formats: PDF, DOC, DOCX (max 5 MB).
Do NOT commit actual resume files to version control.
Add this folder to .gitignore.
