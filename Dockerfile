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

# Switch to non-root user
USER appuser

EXPOSE 8000

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "2", "run:app"]
