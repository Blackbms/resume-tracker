# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Purpose

A Flask web application to track job applications — where resumes have been sent and responses from employers.

## Setup

```bash
python -m venv venv
pip install -r requirements.txt
```

Activate the virtual environment (run once per terminal session):

| Shell | Command |
|---|---|
| Command Prompt | `venv\Scripts\activate.bat` |
| PowerShell | `venv\Scripts\Activate.ps1` |
| Git Bash | `source venv/Scripts/activate` |

## Running the App

```bash
python run.py
```

Then open http://127.0.0.1:5000 in a browser.

## Architecture

```
run.py              # Entry point — creates and runs the Flask app
config.py           # Configuration (database URL, secret key)
app/
  __init__.py       # App factory (create_app), initializes Flask + SQLAlchemy
  models.py         # SQLAlchemy models (JobApplication)
  routes.py         # All URL routes, grouped in a Blueprint called `main`
  templates/        # Jinja2 HTML templates
    base.html       # Shared layout and CSS
    index.html      # Job list
    add_job.html    # Add application form
    job_detail.html # View / edit / delete a single application
```

The app uses the **application factory pattern** (`create_app()`). `db` is initialized in `app/__init__.py` and imported by models and routes.

## Database

Defaults to SQLite (`resume_tracker.db` in the project root). To switch databases, set the `DATABASE_URL` environment variable before running:

```bat
# Command Prompt
set DATABASE_URL=postgresql://user:password@host/dbname
python run.py

# PowerShell
$env:DATABASE_URL="postgresql://user:password@host/dbname"
python run.py
```

Use `mysql+pymysql://...` as the prefix for MySQL.

The database schema is created automatically on first run via `db.create_all()`.

## Key Design Decisions

- **SQLAlchemy ORM** is used so the database backend can be swapped without touching application code.
- All routes live in a single Blueprint (`app/routes.py`) — split into multiple blueprints only if the app grows significantly.
- Job status values are defined as `JobApplication.STATUSES` in the model so templates and routes always use the same list.
