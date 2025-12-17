#!/bin/bash
set -e

echo "Waiting for postgres..."
while ! pg_isready -h localhost -p 5432 -U postgres; do
  sleep 1
done
echo "PostgreSQL started"

echo "Running migrations..."
python manage.py migrate

echo "Checking for power outage..."
python manage.py check_outage || true

echo "Starting Celery worker in background..."
celery -A config worker -l warning &

echo "Starting Celery beat in background..."
celery -A config beat -l warning &

echo "Starting Django development server..."
python manage.py runserver 0.0.0.0:8000 --verbosity 2
