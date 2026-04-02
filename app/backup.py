import json
import os
import logging
from datetime import datetime, date
from pathlib import Path
from sqlalchemy import text, inspect
from flask import current_app
from app import db
from app.models import JobApplication

logger = logging.getLogger('resume_tracker')


def _get_backup_dir():
    """Get backup directory path, container-friendly.

    Priority:
    1. BACKUP_DIR environment variable
    2. Default to /app/backups in containers
    3. Default to project_root/backups locally
    """
    # Check for explicit environment variable
    if os.environ.get('BACKUP_DIR'):
        return Path(os.environ['BACKUP_DIR'])

    # Try to get project root from Flask app context
    try:
        if current_app:
            project_root = Path(current_app.root_path).parent
            return project_root / 'backups'
    except:
        pass

    # Container default
    backup_path = Path('/app/backups')
    if backup_path.parent.exists():  # /app directory exists (container env)
        return backup_path

    # Local fallback
    return Path.cwd() / 'backups'


def _ensure_backup_dir():
    """Create backups directory if it doesn't exist."""
    backup_dir = _get_backup_dir()
    backup_dir.mkdir(exist_ok=True, parents=True)
    return backup_dir


def _get_backup_path(format_type):
    """Generate timestamped backup file path."""
    backup_dir = _ensure_backup_dir()
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    filename = f'backup_{timestamp}.{format_type}'
    return backup_dir / filename


def _get_backups_list():
    """Return list of existing backup files with metadata."""
    backup_dir = _ensure_backup_dir()
    if not backup_dir.exists():
        return []

    backups = []
    for file in sorted(backup_dir.glob('backup_*'), reverse=True):
        backups.append({
            'name': file.name,
            'path': str(file),
            'size': file.stat().st_size,
            'created': datetime.fromtimestamp(file.stat().st_mtime)
        })
    return backups


def _serialize_job(job):
    """Convert JobApplication model to JSON-serializable dict."""
    return {
        'id': job.id,
        'company': job.company,
        'role': job.role,
        'date_applied': job.date_applied.isoformat() if job.date_applied else None,
        'status': job.status,
        'job_url': job.job_url,
        'contact_email': job.contact_email,
        'last_contact_date': job.last_contact_date.isoformat() if job.last_contact_date else None,
        'notes': job.notes,
    }


def export_to_json(output_path=None):
    """Export all JobApplication records to JSON file.

    Args:
        output_path: Optional custom path. Defaults to backups/backup_YYYY-MM-DD_HH-MM-SS.json

    Returns:
        Path to created backup file
    """
    if not output_path:
        output_path = _get_backup_path('json')

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    jobs = JobApplication.query.all()
    data = {
        'backup_timestamp': datetime.now().isoformat(),
        'records_count': len(jobs),
        'records': [_serialize_job(job) for job in jobs]
    }

    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)

    logger.info(f'Exported {len(jobs)} records to JSON: {output_path.name}')
    return str(output_path)


def export_to_sql(output_path=None):
    """Export entire database as SQL dump.

    Args:
        output_path: Optional custom path. Defaults to backups/backup_YYYY-MM-DD_HH-MM-SS.sql

    Returns:
        Path to created backup file
    """
    if not output_path:
        output_path = _get_backup_path('sql')

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Get database connection and metadata
    conn = db.engine.raw_connection()
    engine_url = str(db.engine.url)
    dialect_name = db.engine.dialect.name

    sql_statements = []

    # Add header
    sql_statements.append(f'-- Database backup created at {datetime.now().isoformat()}')
    sql_statements.append(f'-- Database type: {dialect_name}')
    sql_statements.append('')

    # For SQLite, use .dump functionality via raw SQL
    if dialect_name == 'sqlite':
        cursor = conn.cursor()
        # Get CREATE TABLE statement
        cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='job_applications'")
        create_table = cursor.fetchone()
        if create_table:
            sql_statements.append(create_table[0] + ';')
            sql_statements.append('')

        # Get all INSERT statements
        jobs = JobApplication.query.all()
        for job in jobs:
            # Escape single quotes for SQL
            company = job.company.replace("'", "''")
            role = job.role.replace("'", "''")
            job_url = job.job_url.replace("'", "''") if job.job_url else None
            contact_email = job.contact_email.replace("'", "''") if job.contact_email else None
            notes = job.notes.replace("'", "''") if job.notes else None

            # Build NULL-safe values
            job_url_val = f"'{job_url}'" if job_url else 'NULL'
            contact_email_val = f"'{contact_email}'" if contact_email else 'NULL'
            last_contact_val = f"'{job.last_contact_date}'" if job.last_contact_date else 'NULL'
            notes_val = f"'{notes}'" if notes else 'NULL'

            insert_sql = f"""INSERT INTO job_applications (id, company, role, date_applied, status, job_url, contact_email, last_contact_date, notes)
VALUES ({job.id}, '{company}', '{role}', '{job.date_applied}', '{job.status}', {job_url_val}, {contact_email_val}, {last_contact_val}, {notes_val});"""
            sql_statements.append(insert_sql)

    elif dialect_name == 'postgresql':
        # PostgreSQL-specific export
        sql_statements.append('DROP TABLE IF EXISTS job_applications CASCADE;')
        sql_statements.append('')

        inspector = inspect(db.engine)
        columns = inspector.get_columns('job_applications')
        create_sql = 'CREATE TABLE job_applications ('
        col_defs = []
        for col in columns:
            col_type = str(col['type'])
            nullable = 'NOT NULL' if not col['nullable'] else 'NULL'
            col_defs.append(f"    {col['name']} {col_type} {nullable}")
        create_sql += ',\n'.join(col_defs) + '\n);'
        sql_statements.append(create_sql)
        sql_statements.append('')

        jobs = JobApplication.query.all()
        for job in jobs:
            # Build values with proper escaping
            company_val = job.company.replace("'", "''") if job.company else None
            role_val = job.role.replace("'", "''") if job.role else None
            job_url_val = job.job_url.replace("'", "''") if job.job_url else None
            contact_email_val = job.contact_email.replace("'", "''") if job.contact_email else None
            notes_val = job.notes.replace("'", "''") if job.notes else None

            values = [
                str(job.id),
                f"'{company_val}'" if company_val else 'NULL',
                f"'{role_val}'" if role_val else 'NULL',
                f"'{job.date_applied}'" if job.date_applied else 'NULL',
                f"'{job.status}'" if job.status else 'NULL',
                f"'{job_url_val}'" if job_url_val else 'NULL',
                f"'{contact_email_val}'" if contact_email_val else 'NULL',
                f"'{job.last_contact_date}'" if job.last_contact_date else 'NULL',
                f"'{notes_val}'" if notes_val else 'NULL',
            ]
            sql_statements.append(f"INSERT INTO job_applications VALUES ({', '.join(values)});")

    elif dialect_name == 'mysql':
        # MySQL-specific export
        sql_statements.append('DROP TABLE IF EXISTS `job_applications`;')
        sql_statements.append('')

        inspector = inspect(db.engine)
        columns = inspector.get_columns('job_applications')
        create_sql = 'CREATE TABLE `job_applications` ('
        col_defs = []
        for col in columns:
            col_type = str(col['type'])
            nullable = 'NOT NULL' if not col['nullable'] else 'NULL'
            col_defs.append(f"  `{col['name']}` {col_type} {nullable}")
        create_sql += ',\n'.join(col_defs) + '\n);'
        sql_statements.append(create_sql)
        sql_statements.append('')

        jobs = JobApplication.query.all()
        for job in jobs:
            # Build values with proper escaping
            company_val = job.company.replace("'", "''") if job.company else None
            role_val = job.role.replace("'", "''") if job.role else None
            job_url_val = job.job_url.replace("'", "''") if job.job_url else None
            contact_email_val = job.contact_email.replace("'", "''") if job.contact_email else None
            notes_val = job.notes.replace("'", "''") if job.notes else None

            values = [
                str(job.id),
                f"'{company_val}'" if company_val else 'NULL',
                f"'{role_val}'" if role_val else 'NULL',
                f"'{job.date_applied}'" if job.date_applied else 'NULL',
                f"'{job.status}'" if job.status else 'NULL',
                f"'{job_url_val}'" if job_url_val else 'NULL',
                f"'{contact_email_val}'" if contact_email_val else 'NULL',
                f"'{job.last_contact_date}'" if job.last_contact_date else 'NULL',
                f"'{notes_val}'" if notes_val else 'NULL',
            ]
            sql_statements.append(f"INSERT INTO `job_applications` VALUES ({', '.join(values)});")

    conn.close()

    # Write to file
    with open(output_path, 'w') as f:
        f.write('\n'.join(sql_statements))

    logger.info(f'Exported database to SQL: {Path(output_path).name}')
    return str(output_path)


def import_from_json(file_path):
    """Import JobApplication records from JSON file.

    Clears existing records before importing.

    Args:
        file_path: Path to JSON backup file

    Returns:
        Tuple of (success: bool, message: str, count: int)
    """
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)

        if not isinstance(data, dict) or 'records' not in data:
            return False, 'Invalid JSON format: missing "records" key', 0

        records = data['records']
        if not isinstance(records, list):
            return False, 'Invalid JSON format: "records" must be a list', 0

        # Clear existing records
        db.session.query(JobApplication).delete()

        # Import new records
        for record in records:
            try:
                job = JobApplication(
                    company=record['company'],
                    role=record['role'],
                    date_applied=date.fromisoformat(record['date_applied']) if record['date_applied'] else None,
                    status=record['status'],
                    job_url=record.get('job_url'),
                    contact_email=record.get('contact_email'),
                    last_contact_date=date.fromisoformat(record['last_contact_date']) if record.get('last_contact_date') else None,
                    notes=record.get('notes'),
                )
                db.session.add(job)
            except (KeyError, ValueError) as e:
                db.session.rollback()
                return False, f'Error parsing record: {str(e)}', 0

        db.session.commit()
        logger.info(f'Successfully imported {len(records)} records from JSON')
        return True, f'Successfully imported {len(records)} records', len(records)

    except FileNotFoundError:
        logger.error(f'Backup file not found: {file_path}')
        return False, f'File not found: {file_path}', 0
    except json.JSONDecodeError as e:
        logger.error(f'Invalid JSON file: {str(e)}')
        return False, f'Invalid JSON file: {str(e)}', 0
    except Exception as e:
        logger.error(f'Error importing from JSON: {str(e)}')
        db.session.rollback()
        return False, f'Error importing from JSON: {str(e)}', 0


def import_from_sql(file_path):
    """Import database from SQL dump file.

    Args:
        file_path: Path to SQL backup file

    Returns:
        Tuple of (success: bool, message: str)
    """
    try:
        with open(file_path, 'r') as f:
            sql_content = f.read()

        # Split by semicolons and execute each statement
        conn = db.engine.raw_connection()
        cursor = conn.cursor()

        # Split statements and execute
        statements = [s.strip() for s in sql_content.split(';') if s.strip() and not s.strip().startswith('--')]

        for statement in statements:
            if statement:
                try:
                    cursor.execute(statement)
                except Exception as e:
                    conn.rollback()
                    conn.close()
                    return False, f'Error executing SQL: {str(e)}'

        conn.commit()
        conn.close()
        logger.info(f'Successfully imported database from SQL dump')
        return True, 'Successfully imported from SQL dump'

    except FileNotFoundError:
        logger.error(f'SQL dump file not found: {file_path}')
        return False, f'File not found: {file_path}'
    except Exception as e:
        logger.error(f'Error importing from SQL: {str(e)}')
        return False, f'Error importing from SQL: {str(e)}'
