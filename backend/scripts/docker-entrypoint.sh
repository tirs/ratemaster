#!/bin/bash
set -e

# Wait for PostgreSQL
echo "Waiting for PostgreSQL..."
python scripts/wait_for_db.py || exit 1

# Run migrations
echo "Running migrations..."
alembic upgrade head

# Optionally create admin (if env vars set)
if [ -n "$ADMIN_EMAIL" ] && [ -n "$ADMIN_PASSWORD" ]; then
  echo "Creating admin user..."
  python -m scripts.create_admin || true
fi

# Run the main command
exec "$@"
