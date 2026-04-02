import logging
from logging.handlers import RotatingFileHandler
import os
from pathlib import Path
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import Config

db = SQLAlchemy()

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
