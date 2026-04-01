from datetime import date
from flask import Blueprint, render_template, request, redirect, url_for, abort
from app import db
from app.models import JobApplication

main = Blueprint('main', __name__)


@main.route('/')
def index():
    sort = request.args.get('sort', 'company')
    direction = request.args.get('dir', 'asc')

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
