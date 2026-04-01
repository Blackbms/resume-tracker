from datetime import date
from app import db

class JobApplication(db.Model):
    __tablename__ = 'job_applications'

    id = db.Column(db.Integer, primary_key=True)
    company = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(200), nullable=False)
    date_applied = db.Column(db.Date, nullable=False, default=date.today)
    status = db.Column(db.String(50), nullable=False, default='Applied')
    job_url = db.Column(db.String(500))
    contact_email = db.Column(db.String(200))
    last_contact_date = db.Column(db.Date)
    notes = db.Column(db.Text)

    # Valid status values
    STATUSES = [
        'Applied',
        'No Response',
        'Interview Scheduled',
        'Interview Completed',
        'Offer Received',
        'Rejected',
        'Withdrawn',
    ]

    def __repr__(self):
        return f'<JobApplication {self.company} - {self.role}>'
