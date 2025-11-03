import os
import sys

# Add the project directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

# Set the Django settings module for production
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'akilimo_nigeria.settings.production')

# Import Django WSGI application
from django.core.wsgi import get_wsgi_application

# Create the WSGI application
application = get_wsgi_application()