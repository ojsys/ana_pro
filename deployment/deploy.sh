#!/bin/bash

# AKILIMO Nigeria Association - Production Deployment Script
# This script handles the deployment to cPanel hosting

set -e  # Exit on any error

echo "🚀 Starting AKILIMO Nigeria Association deployment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if .env file exists
if [ ! -f ".env" ]; then
    print_error ".env file not found! Please copy .env.example to .env and configure it."
    exit 1
fi

# Load environment variables
source .env

# Validate required environment variables
required_vars=("SECRET_KEY" "DB_NAME" "DB_USER" "DB_PASSWORD" "SITE_URL")
for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        print_error "Environment variable $var is not set!"
        exit 1
    fi
done

print_status "Environment variables validated ✓"

# Install/Update dependencies
print_status "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Set Django settings module for production
export DJANGO_SETTINGS_MODULE=akilimo_nigeria.settings.production

# Run database migrations
print_status "Running database migrations..."
python manage.py migrate --noinput

# Create cache table if using database cache
print_status "Creating cache table..."
python manage.py createcachetable cache_table || true

# Collect static files
print_status "Collecting static files..."
python manage.py collectstatic --noinput --clear

# Create superuser if it doesn't exist (optional)
if [ "${CREATE_SUPERUSER:-false}" = "true" ]; then
    print_status "Creating superuser..."
    python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', '${ADMIN_EMAIL}', '${ADMIN_PASSWORD}')
    print('Superuser created successfully')
else:
    print('Superuser already exists')
"
fi

# Create logs directory
print_status "Creating logs directory..."
mkdir -p logs
chmod 755 logs

# Run system checks
print_status "Running Django system checks..."
python manage.py check --deploy

# Test database connection
print_status "Testing database connection..."
python manage.py shell -c "
from django.db import connection
cursor = connection.cursor()
print('Database connection successful')
"

print_status "✅ Deployment completed successfully!"
print_warning "Don't forget to:"
print_warning "  1. Set up your web server to serve static files"
print_warning "  2. Configure your domain's DNS settings"
print_warning "  3. Set up SSL certificate"
print_warning "  4. Configure backups"
print_warning "  5. Set up monitoring"

echo -e "${GREEN}🎉 AKILIMO Nigeria Association is ready to serve!${NC}"