FROM python:3.12-slim

LABEL org.opencontainers.image.source=https://github.com/Blackbms/resume-tracker

# Create a non-root user
RUN useradd --create-home appuser

WORKDIR /app

# Install dependencies first for better layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create backups and logs directories and ensure appuser can write to them
RUN mkdir -p /app/backups /app/logs && chown -R appuser:appuser /app/backups /app/logs && chmod 755 /app/backups /app/logs

# Switch to non-root user
USER appuser

EXPOSE 8000

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "2", "run:app"]
