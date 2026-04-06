import logging
from logging.handlers import RotatingFileHandler
import os
from pathlib import Path
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from config import Config

db = SQLAlchemy()


def _migrate_add_is_processed_column(engine):
    """Add is_processed column to job_applications table if it doesn't exist."""
    dialect_name = engine.dialect.name

    try:
        with engine.begin() as conn:
            if dialect_name == 'sqlite':
                result = conn.execute(text('PRAGMA table_info(job_applications)'))
                columns = [row[1] for row in result.fetchall()]
                if 'is_processed' not in columns:
                    conn.execute(text('ALTER TABLE job_applications ADD COLUMN is_processed INTEGER DEFAULT 0'))
            elif dialect_name == 'postgresql':
                # Check if column exists in PostgreSQL
                result = conn.execute(text(
                    "SELECT column_name FROM information_schema.columns WHERE table_name='job_applications' AND column_name='is_processed'"
                ))
                if not result.fetchone():
                    conn.execute(text('ALTER TABLE job_applications ADD COLUMN is_processed BOOLEAN DEFAULT FALSE'))
            elif dialect_name == 'mysql':
                # For MySQL
                result = conn.execute(text(
                    "SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME='job_applications' AND COLUMN_NAME='is_processed'"
                ))
                if not result.fetchone():
                    conn.execute(text('ALTER TABLE job_applications ADD COLUMN is_processed BOOLEAN DEFAULT FALSE'))
    except Exception as e:
        # Column already exists or other issue, log and continue
        app_logger = logging.getLogger('resume_tracker')
        app_logger.debug(f"Migration note: {str(e)}")


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)

    from app.routes import main
    app.register_blueprint(main)

    # Register CLI commands
    from app.backup_cli import backup
    app.cli.add_command(backup)

    # Setup logging
    _setup_logging(app)

    with app.app_context():
        db.create_all()
        _migrate_add_is_processed_column(db.engine)

    return app


def _setup_logging(app):
    """Configure application logging with rotating file handler."""
    # Get log directory (container-friendly)
    if os.environ.get('LOG_DIR'):
        log_dir = Path(os.environ['LOG_DIR'])
    elif Path('/app').exists():  # Container environment
        log_dir = Path('/app/logs')
    else:  # Local development
        log_dir = Path(app.root_path).parent / 'logs'

    log_dir.mkdir(exist_ok=True, parents=True)

    # Create logger
    logger = logging.getLogger('resume_tracker')
    logger.setLevel(logging.DEBUG)

    # Only add handlers if they don't already exist (avoid duplicate logs)
    if not logger.handlers:
        # Rotating file handler
        log_file = log_dir / 'app.log'
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10485760,  # 10MB
            backupCount=10
        )
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(
            '%(levelname)s: %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)

    # Set Flask's logger to use our logger
    app.logger.handlers = logger.handlers
    app.logger.setLevel(logger.level)
