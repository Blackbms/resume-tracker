from datetime import date
from flask import Blueprint, render_template, request, redirect, url_for, abort, flash, send_file, current_app, session
from pathlib import Path
from app import db
from app.models import JobApplication
from app.backup import (
    export_to_json, export_to_sql, import_from_json, import_from_sql, _get_backups_list, _get_backup_dir
)

main = Blueprint('main', __name__)


@main.route('/')
def index():
    # Check if sort/direction are in URL params; if so, update session
    if 'sort' in request.args:
        session['sort'] = request.args.get('sort')
    if 'dir' in request.args:
        session['direction'] = request.args.get('dir')

    # Fall back to session, then to defaults
    sort = session.get('sort', 'date_applied')
    direction = session.get('direction', 'asc')

    columns = {
        'company': JobApplication.company,
        'date_applied': JobApplication.date_applied,
        'last_contact': JobApplication.last_contact_date,
    }
    col = columns.get(sort, JobApplication.date_applied)
    order = col.desc() if direction == 'desc' else col.asc()

    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')

    query = JobApplication.query
    if date_from:
        query = query.filter(JobApplication.date_applied >= date.fromisoformat(date_from))
    if date_to:
        query = query.filter(JobApplication.date_applied <= date.fromisoformat(date_to))

    jobs = query.order_by(order).all()
    return render_template('index.html', jobs=jobs, sort=sort, direction=direction,
                           date_from=date_from, date_to=date_to)


@main.route('/add', methods=['GET', 'POST'])
def add_job():
    if request.method == 'POST':
        job = JobApplication(
            company=request.form['company'],
            role=request.form['role'],
            date_applied=date.fromisoformat(request.form['date_applied']),
            status=request.form['status'],
            job_url=request.form.get('job_url') or None,
            contact_email=request.form.get('contact_email') or None,
            last_contact_date=date.fromisoformat(request.form['last_contact_date']) if request.form.get('last_contact_date') else date.fromisoformat(request.form['date_applied']),
            notes=request.form.get('notes') or None,
        )
        db.session.add(job)
        db.session.commit()
        return redirect(url_for('main.index'))

    return render_template('add_job.html',
                           statuses=JobApplication.STATUSES,
                           today=date.today().isoformat())


@main.route('/job/<int:job_id>')
def job_detail(job_id):
    job = JobApplication.query.get_or_404(job_id)
    return render_template('job_detail.html', job=job, statuses=JobApplication.STATUSES)


@main.route('/job/<int:job_id>/update', methods=['POST'])
def update_job(job_id):
    job = JobApplication.query.get_or_404(job_id)
    job.company = request.form['company']
    job.role = request.form['role']
    job.date_applied = date.fromisoformat(request.form['date_applied'])
    job.status = request.form['status']
    job.job_url = request.form.get('job_url') or None
    job.contact_email = request.form.get('contact_email') or None
    job.last_contact_date = date.fromisoformat(request.form['last_contact_date']) if request.form.get('last_contact_date') else None
    job.notes = request.form.get('notes') or None
    db.session.commit()
    return redirect(url_for('main.job_detail', job_id=job.id))


@main.route('/job/<int:job_id>/delete', methods=['POST'])
def delete_job(job_id):
    job = JobApplication.query.get_or_404(job_id)
    db.session.delete(job)
    db.session.commit()
    return redirect(url_for('main.index'))


@main.route('/backup')
def backup_manage():
    """Show backup management page."""
    backups = _get_backups_list()
    return render_template('backup.html', backups=backups)


@main.route('/backup/export', methods=['POST'])
def backup_export():
    """Export database in requested format."""
    format_type = request.form.get('format', 'json')

    try:
        if format_type == 'json':
            path = export_to_json()
            flash(f'Database exported to JSON: {Path(path).name}', 'success')
        elif format_type == 'sql':
            path = export_to_sql()
            flash(f'Database exported to SQL: {Path(path).name}', 'success')
        elif format_type == 'both':
            json_path = export_to_json()
            sql_path = export_to_sql()
            flash(f'Database exported to both formats', 'success')
        else:
            flash('Invalid format specified', 'error')
    except Exception as e:
        flash(f'Export failed: {str(e)}', 'error')

    return redirect(url_for('main.backup_manage'))


@main.route('/backup/import', methods=['POST'])
def backup_import():
    """Import database from uploaded file."""
    if 'backup_file' not in request.files:
        flash('No file provided', 'error')
        return redirect(url_for('main.backup_manage'))

    file = request.files['backup_file']
    if not file or file.filename == '':
        flash('No file selected', 'error')
        return redirect(url_for('main.backup_manage'))

    try:
        # Save uploaded file temporarily
        backup_dir = _get_backup_dir()
        backup_dir.mkdir(exist_ok=True, parents=True)
        temp_path = backup_dir / file.filename

        file.save(temp_path)

        # Determine format and import
        if temp_path.suffix == '.json':
            success, message, count = import_from_json(str(temp_path))
            if success:
                flash(f'Successfully imported {count} records from JSON', 'success')
            else:
                flash(f'Import failed: {message}', 'error')
        elif temp_path.suffix == '.sql':
            success, message = import_from_sql(str(temp_path))
            if success:
                flash(message, 'success')
            else:
                flash(f'Import failed: {message}', 'error')
        else:
            flash('Unsupported file format. Use .json or .sql', 'error')

    except Exception as e:
        flash(f'Import error: {str(e)}', 'error')

    return redirect(url_for('main.backup_manage'))


@main.route('/backup/download/<filename>')
def backup_download(filename):
    """Download a backup file."""
    # Get backup directory path
    backup_path = _get_backup_dir() / filename

    # Security check: ensure file is in backups directory
    if not backup_path.exists() or not backup_path.is_file():
        abort(404)

    # Prevent directory traversal
    if '..' in filename or filename.startswith('/'):
        abort(403)

    return send_file(backup_path, as_attachment=True)


@main.route('/backup/delete/<filename>', methods=['POST'])
def backup_delete(filename):
    """Delete a backup file."""
    # Get backup directory path
    backup_path = _get_backup_dir() / filename

    # Security check: ensure file is in backups directory
    if not backup_path.exists() or not backup_path.is_file():
        flash('Backup file not found', 'error')
        return redirect(url_for('main.backup_manage'))

    # Prevent directory traversal
    if '..' in filename or filename.startswith('/'):
        abort(403)

    try:
        backup_path.unlink()
        flash(f'Deleted: {filename}', 'success')
    except Exception as e:
        flash(f'Failed to delete: {str(e)}', 'error')

    return redirect(url_for('main.backup_manage'))
