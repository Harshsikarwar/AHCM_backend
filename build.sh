#!/usr/bin/env bash
set -o errexit

echo "Current directory:"
pwd

echo "Repository contents:"
ls -la

cd HCM

echo "Current directory after cd:"
pwd

echo "Installing dependencies..."
pip install -r ../requirements.txt

echo "Collecting static files..."
python manage.py collectstatic --no-input

echo "Running migrations..."
python manage.py migrate --no-input