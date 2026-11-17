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

## Deploy on Streamlit Community Cloud

This project uses Streamlit and should be deployed on Streamlit Community Cloud, not Vercel.

1. Sign in to [Streamlit Community Cloud](https://share.streamlit.io/).
2. Select **Create app** and choose the `monishlege/samsung` repository and `main` branch.
3. Set the main file path to `app.py`, then deploy.

Dependencies are listed in `requirements.txt`. The SQLite database is created on startup; data stored on a hosted instance may not persist across restarts.

## Demo accounts
| Role | Username | Password |
|---|---|---|
| Admin | admin | admin123 |
| Student | student | student123 |
| Faculty | faculty | faculty123 |
| Maintenance | staff | staff123 |

## Important
This is a local academic prototype. The included AI engine uses explainable keyword and text-similarity rules; it is not a trained machine-learning model. Passwords are stored as plain text for demo simplicity. Before real deployment, add password hashing, secure sessions, authorization tests, backups and a proper production database.
