FROM python:3.11-slim

WORKDIR /app

# Install system deps for psycopg2
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create uploads directory for org logos (volume mount overrides at runtime)
RUN mkdir -p /app/uploads/org_logos

# Make entrypoint executable
RUN chmod +x scripts/docker-entrypoint.sh

# Expose port
EXPOSE 30080

# Entrypoint: wait for DB, run migrations, then exec main command
ENTRYPOINT ["/app/scripts/docker-entrypoint.sh"]

# Default: run uvicorn (overridden in docker-compose for celery)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "30080"]
