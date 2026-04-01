# Resume Tracker

A lightweight Flask web app for tracking job applications — where you've applied, the current status, and when you last heard back.

## Features

- Add, edit, and delete job applications
- Track company, role, date applied, status, job URL, contact email, and date of last contact
- Sort the application list by company, date applied, or last contact (click any column header)
- Filter applications by date applied range
- Status options: Applied, No Response, Interview Scheduled, Interview Completed, Offer Received, Rejected, Withdrawn

## Requirements

- Python 3.9+
- pip

## Local Setup

1. **Clone the repository**

   ```bash
   git clone <repo-url>
   cd resume-tracker
   ```

2. **Create and activate a virtual environment**

   ```bash
   python3 -m venv venv
   ```

   | Shell | Activate command |
   |---|---|
   | bash / zsh | `source venv/bin/activate` |
   | Command Prompt | `venv\Scripts\activate.bat` |
   | PowerShell | `venv\Scripts\Activate.ps1` |
   | Git Bash | `source venv/Scripts/activate` |

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Run the app**

   ```bash
   python run.py
   ```

5. **Open in your browser**

   ```
   http://127.0.0.1:5000
   ```

The SQLite database (`instance/resume_tracker.db`) is created automatically on first run — no setup required.

## Configuration

The app defaults to SQLite. To use a different database, set the `DATABASE_URL` environment variable before running:

```bash
# PostgreSQL
export DATABASE_URL=postgresql://user:password@host/dbname

# MySQL
export DATABASE_URL=mysql+pymysql://user:password@host/dbname

python run.py
```

## Project Structure

```
run.py              # Entry point
config.py           # Configuration (database URL, secret key)
app/
  __init__.py       # App factory (create_app)
  models.py         # SQLAlchemy models
  routes.py         # URL routes
  templates/
    base.html       # Shared layout and styles
    index.html      # Application list with sorting and filtering
    add_job.html    # Add application form
    job_detail.html # View / edit / delete a single application
```
