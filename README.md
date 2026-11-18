# CampusConnect AI

A beginner-friendly campus complaint and facilities management dashboard built with Python, Streamlit and SQLite.

## Features
- Roles: Student, Faculty, Admin and Maintenance Staff
- Secure sign-in, student/faculty registration and admin role management
- Complaint submission and status tracking
- Maintenance Staff resolution submissions with a required completion photo and browser GPS geotag
- Local AI review of resolution notes; a complaint is marked Resolved only when the notes clearly confirm completion
- Automatic local complaint categorization and High/Medium/Low priority assessment from complaint text
- Possible duplicate report detection
- Recurring issue summaries
- Dashboard metrics, filters and user management
- Responsive layout for mobile and tablet screens
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

Dependencies are listed in `requirements.txt`. Add the initial administrator credentials in the app's Streamlit secrets before deployment:

```toml
[auth]
admin_username = "campusadmin"
admin_password = "replace-with-a-unique-password-of-at-least-16-characters"
```

The first configured admin is created only when the database has no administrator. Do not commit credentials or a local `secrets.toml` file. Students and faculty can create accounts from the sign-in page; an administrator assigns Admin or Maintenance Staff roles.

## Sign-in and database

- Passwords are stored as salted PBKDF2 hashes, not plaintext. Passwords must be at least 12 characters; the bootstrap administrator password must be at least 16 characters.
- Sign-in is temporarily locked after five failed attempts for the same username.
- Sessions expire after 30 minutes of inactivity or 12 hours total.
- Students and faculty can only view their own complaints. Admin and Maintenance Staff accounts can view all complaints.
- Only Maintenance Staff can submit a resolution. The local rule-based AI checks the staff member's notes for a clear completion statement; if it cannot confirm the issue is fixed, the complaint stays In Progress and the AI feedback is shown. The AI does not visually analyze the photo. A submission also requires a valid JPEG, PNG, or WebP completion photo (up to 5 MB) and GPS coordinates captured by the staff member's browser/device. Resolution notes, photos, and coordinates are stored in SQLite and shown to the complaint owner, Admin, and Maintenance Staff. Browser location access requires permission and a secure context (HTTPS or localhost).
- The default SQLite file is `campus.db` beside the application. Set `CAMPUS_DB_PATH` (or `[database].path` in Streamlit secrets) to choose another path.

**SQLite on Streamlit Community Cloud is not production-persistent.** Its local filesystem can be reset and does not provide durable backups or safe shared storage across multiple app instances. This SQLite configuration is suitable for local development or a single server with a persistent disk and managed backups. Before a production deployment on Community Cloud or any multi-instance host, move accounts and complaints to a managed, persistent database and configure backups.

## Important
This remains an academic prototype, not a fully production-ready service. Complaint categorization, priority, and resolution review use explainable local keyword rules, not a trained model or external AI service. Resolution review checks text notes only; it cannot verify repair quality from the photo. Before handling real campus data, add a persistent managed database, automated backups, email verification, password reset and MFA policies, operational monitoring, and a privacy review.
