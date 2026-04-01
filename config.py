import os

class Config:
    # Default to SQLite for local development.
    # To switch databases, set the DATABASE_URL environment variable:
    #   MySQL:      mysql+pymysql://user:password@host/dbname
    #   PostgreSQL: postgresql://user:password@host/dbname
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///resume_tracker.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key'
