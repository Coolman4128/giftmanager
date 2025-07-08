#!/bin/bash

set -e

echo "Starting Django application setup..."

# Ensure data directory exists and has proper permissions
mkdir -p /app/data
chmod 755 /app/data

# Wait for any external services (if needed)
echo "Checking database connectivity..."

# Check if database file exists, if not create it
DB_PATH="${DATABASE_PATH:-/app/data/db.sqlite3}"
DB_DIR=$(dirname "$DB_PATH")

# Ensure the database directory exists and is writable
if [ ! -d "$DB_DIR" ]; then
    echo "Creating database directory at $DB_DIR"
    mkdir -p "$DB_DIR"
    chmod 755 "$DB_DIR"
fi

# Create the database file if it doesn't exist
if [ ! -f "$DB_PATH" ]; then
    echo "Creating database file at $DB_PATH"
    touch "$DB_PATH"
    chmod 664 "$DB_PATH"
else
    echo "Database file already exists at $DB_PATH"
    # Ensure proper permissions on existing database file
    chmod 664 "$DB_PATH"
fi

# Verify we can write to the database file
if [ ! -w "$DB_PATH" ]; then
    echo "ERROR: Cannot write to database file $DB_PATH"
    ls -la "$DB_PATH"
    exit 1
fi

echo "Database file permissions verified"

# Apply database migrations
echo "Applying database migrations..."
python manage.py makemigrations --noinput
python manage.py migrate --noinput

# Load any initial data (fixtures)
echo "Loading initial data if available..."
if [ -f "fixtures/initial_data.json" ]; then
    python manage.py loaddata fixtures/initial_data.json
fi

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput --clear

# Create superuser if it doesn't exist
echo "Creating superuser if needed..."
python manage.py shell -c "
import os
from django.contrib.auth import get_user_model
User = get_user_model()
admin_username = os.environ.get('ADMIN_USERNAME', 'admin')
admin_email = os.environ.get('ADMIN_EMAIL', 'admin@example.com')
admin_password = os.environ.get('ADMIN_PASSWORD', 'admin123')

if not User.objects.filter(username=admin_username).exists():
    User.objects.create_superuser(admin_username, admin_email, admin_password)
    print(f'Superuser created: {admin_username}/{admin_password}')
else:
    print(f'Superuser {admin_username} already exists')
"

# Run Django checks
echo "Running Django system checks..."
python manage.py check --deploy

echo "Django setup completed successfully!"

# Start Gunicorn
echo "Starting Gunicorn server..."
exec gunicorn \
    --bind 0.0.0.0:8000 \
    --workers 3 \
    --worker-class sync \
    --worker-connections 1000 \
    --max-requests 1000 \
    --max-requests-jitter 100 \
    --timeout 30 \
    --keep-alive 2 \
    --log-level info \
    --access-logfile - \
    --error-logfile - \
    giftmanager.wsgi:application
