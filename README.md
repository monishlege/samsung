# CampusConnect AI

A beginner-friendly campus complaint and facilities management dashboard built with Python, Streamlit and SQLite.

## Features
- Roles: Student, Faculty, Admin and Maintenance Staff
- Complaint submission and status tracking
- AI-assisted category and priority suggestions (keyword-based starter engine)
- Possible duplicate report detection
- Recurring issue summaries
- Dashboard metrics, filters and user management
- SQLite database created automatically

## Run locally (Windows PowerShell)

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app.py
```

If PowerShell blocks activation, run:
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

## Demo accounts
| Role | Username | Password |
|---|---|---|
| Admin | admin | admin123 |
| Student | student | student123 |
| Faculty | faculty | faculty123 |
| Maintenance | staff | staff123 |

## Important
This is a local academic prototype. The included AI engine uses explainable keyword and text-similarity rules; it is not a trained machine-learning model. Passwords are stored as plain text for demo simplicity. Before real deployment, add password hashing, secure sessions, authorization tests, backups and a proper production database.
