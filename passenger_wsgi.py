#!/usr/bin/python3.9
"""
cPanel Python App Entry Point for AKILIMO Nigeria Association
This file is required by cPanel's Python App hosting
"""

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

# cPanel specific: Ensure proper handling of static files
try:
    # Try to import and setup static file handling
    from django.conf import settings
    if hasattr(settings, 'STATIC_ROOT'):
        # Ensure static root exists
        import os
        if not os.path.exists(settings.STATIC_ROOT):
            os.makedirs(settings.STATIC_ROOT, exist_ok=True)
except Exception as e:
    # Log any issues but don't break the app
    import logging
    logging.error(f"Static file setup issue: {e}")