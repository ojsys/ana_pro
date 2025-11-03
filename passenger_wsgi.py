#!/usr/bin/env python
"""
WSGI config for AKILIMO Nigeria Association project.

This module contains the WSGI application used by Django's development server
and any production WSGI deployments. It should expose a module-level variable
named ``application``. Django's ``runserver`` and ``runfcgi`` commands discover
this application via the ``WSGI_APPLICATION`` setting.
"""
import os
import sys

# Add the project directory to Python path
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)

# Set the Django settings module for production
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'akilimo_nigeria.settings.production')

# This application object is used by the WSGI server to handle requests
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()