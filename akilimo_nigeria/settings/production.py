"""
Production settings for AKILIMO Nigeria Association project.
Optimized for cPanel hosting environment.
"""

from .base import *
from decouple import config
import os

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY')  # Must be set in environment

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', default=False, cast=bool)

# Production allowed hosts - must be configured
ALLOWED_HOSTS = config(
    'ALLOWED_HOSTS', 
    default='',
    cast=lambda v: [s.strip() for s in v.split(',') if s.strip()]
)

# Database configuration for production
# Supports both MySQL and PostgreSQL via DATABASE_URL
DATABASE_URL = config('DATABASE_URL', default=None)

if DATABASE_URL:
    # Parse DATABASE_URL for cPanel MySQL
    try:
        import dj_database_url
        DATABASES = {
            'default': dj_database_url.parse(DATABASE_URL)
        }
    except ImportError:
        # Fallback to manual MySQL configuration
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.mysql',
                'NAME': config('DB_NAME'),
                'USER': config('DB_USER'),
                'PASSWORD': config('DB_PASSWORD'),
                'HOST': config('DB_HOST', default='localhost'),
                'PORT': config('DB_PORT', default='3306'),
                'OPTIONS': {
                    'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
                    'charset': 'utf8mb4',
                },
            }
        }
else:
    # Manual database configuration
    DATABASES = {
        'default': {
            'ENGINE': config('DB_ENGINE', default='django.db.backends.mysql'),
            'NAME': config('DB_NAME'),
            'USER': config('DB_USER'),
            'PASSWORD': config('DB_PASSWORD'),
            'HOST': config('DB_HOST', default='localhost'),
            'PORT': config('DB_PORT', default='3306'),
            'OPTIONS': {
                'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
                'charset': 'utf8mb4',
            },
        }
    }

# cPanel MySQL configuration - use PyMySQL as MySQL adapter
try:
    import pymysql
    pymysql.install_as_MySQLdb()
except ImportError:
    pass  # pymysql not available, database might not be configured yet

# Security settings for production
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_SECONDS = config('SECURE_HSTS_SECONDS', default=31536000, cast=int)
SECURE_HSTS_PRELOAD = config('SECURE_HSTS_PRELOAD', default=False, cast=bool)
SECURE_REDIRECT_EXEMPT = []
SECURE_SSL_REDIRECT = config('SECURE_SSL_REDIRECT', default=True, cast=bool)
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Session security
SESSION_COOKIE_SECURE = config('SESSION_COOKIE_SECURE', default=False, cast=bool)
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_AGE = 86400  # 24 hours
SESSION_SAVE_EVERY_REQUEST = True

# CSRF security
CSRF_COOKIE_SECURE = config('CSRF_COOKIE_SECURE', default=True, cast=bool)
CSRF_COOKIE_HTTPONLY = True
CSRF_TRUSTED_ORIGINS = config(
    'CSRF_TRUSTED_ORIGINS',
    default='https://akilimonigeria.org,https://www.akilimonigeria.org',
    cast=lambda v: [s.strip() for s in v.split(',') if s.strip()]
)

# Additional CSRF settings for production
CSRF_COOKIE_SAMESITE = 'Lax'
CSRF_USE_SESSIONS = False  # Use cookies instead of sessions for CSRF tokens

# CORS Configuration for production
CORS_ALLOWED_ORIGINS = config(
    'CORS_ALLOWED_ORIGINS',
    default='',
    cast=lambda v: [s.strip() for s in v.split(',') if s.strip()]
)

CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_ALL_ORIGINS = False  # Never allow all origins in production

# Cache Configuration - Redis for production (if available)
REDIS_URL = config('REDIS_URL', default=None)

if REDIS_URL:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.redis.RedisCache',
            'LOCATION': REDIS_URL,
            'OPTIONS': {
                'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            },
            'TIMEOUT': config('CACHE_TIMEOUT', default=900, cast=int),
        }
    }
else:
    # Fallback to database cache for cPanel
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
            'LOCATION': 'cache_table',
            'TIMEOUT': config('CACHE_TIMEOUT', default=900, cast=int),
        }
    }

# Static files configuration for production
STATIC_URL = config('STATIC_URL', default='/static/')

# cPanel hosting: Use public_html/static for static files
if config('CPANEL_HOSTING', default=False, cast=bool):
    # cPanel typically uses public_html as the web root
    STATIC_ROOT = config('STATIC_ROOT', default='/home/akilimon/public_html/static/')
    # Don't use WhiteNoise on cPanel - let the web server handle static files
else:
    # For other hosting providers (VPS, etc.)
    STATIC_ROOT = config('STATIC_ROOT', default=str(BASE_DIR / 'staticfiles'))
    # Add WhiteNoise for static file serving
    MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Media files configuration for production
MEDIA_URL = config('MEDIA_URL', default='/media/')
MEDIA_ROOT = config('MEDIA_ROOT', default=str(BASE_DIR / 'media'))

# Ensure logs directory exists before configuring logging
LOG_DIR = os.path.dirname(config('LOG_FILE', default='/home/akilimon/ana_pro/logs/akilimo_nigeria.log'))
if not os.path.exists(LOG_DIR):
    try:
        os.makedirs(LOG_DIR, mode=0o755, exist_ok=True)
    except OSError as e:
        # If we can't create the directory, log to console instead
        import sys
        print(f"Warning: Could not create logs directory {LOG_DIR}: {e}", file=sys.stderr)
        print("Logging will be directed to console only.", file=sys.stderr)

# Logging Configuration for production
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'detailed': {
            'format': '[{asctime}] {levelname} [{name}:{lineno}] {message}\n'
                      'Process: {process:d} | Thread: {thread:d} | Module: {module}\n'
                      '{pathname}',
            'style': '{',
            'datefmt': '%Y-%m-%d %H:%M:%S',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        },
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': config('LOG_FILE', default='/home/akilimon/ana_pro/logs/akilimo_nigeria.log'),
            'maxBytes': 1024*1024*15,  # 15MB
            'backupCount': 10,
            'formatter': 'verbose',
        },
        'error_file': {
            'level': 'ERROR',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': config('ERROR_LOG_FILE', default='/home/akilimon/ana_pro/logs/akilimo_nigeria_error.log'),
            'maxBytes': 1024*1024*15,  # 15MB
            'backupCount': 10,
            'formatter': 'detailed',
        },
        'debug_file': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': config('DEBUG_LOG_FILE', default='/home/akilimon/ana_pro/logs/akilimo_nigeria_debug.log'),
            'maxBytes': 1024*1024*20,  # 20MB
            'backupCount': 5,
            'formatter': 'detailed',
        },
        'db_file': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': config('DB_LOG_FILE', default='/home/akilimon/ana_pro/logs/akilimo_nigeria_db.log'),
            'maxBytes': 1024*1024*10,  # 10MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler',
            'include_html': True,
        },
    },
    'root': {
        'handlers': ['file', 'console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'error_file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['error_file', 'mail_admins', 'console'],
            'level': 'ERROR',
            'propagate': False,
        },
        'django.server': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.db.backends': {
            'handlers': ['db_file'],
            'level': config('DB_LOG_LEVEL', default='INFO'),
            'propagate': False,
        },
        'dashboard': {
            'handlers': ['file', 'error_file', 'debug_file', 'console'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'website': {
            'handlers': ['file', 'error_file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# Site URL for production
SITE_URL = config('SITE_URL')  # Must be set in environment

# Email configuration for production
EMAIL_BACKEND = config('EMAIL_BACKEND', default='django.core.mail.backends.smtp.EmailBackend')
EMAIL_HOST = config('EMAIL_HOST')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
EMAIL_USE_SSL = config('EMAIL_USE_SSL', default=False, cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='noreply@akilimo.ng')
SERVER_EMAIL = config('SERVER_EMAIL', default='admin@akilimo.ng')

# Admin email for error notifications
ADMINS = [
    (config('ADMIN_NAME', default='Admin'), config('ADMIN_EMAIL', default='admin@akilimo.ng')),
]

MANAGERS = ADMINS

# File upload settings
FILE_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5MB

# Performance optimizations
USE_THOUSAND_SEPARATOR = True

# Admin URL security (optional - uncomment and change if needed)
# ADMIN_URL = config('ADMIN_URL', default='admin/')

# Sentry configuration (optional - uncomment if using Sentry for error tracking)
# SENTRY_DSN = config('SENTRY_DSN', default=None)
# if SENTRY_DSN:
#     import sentry_sdk
#     from sentry_sdk.integrations.django import DjangoIntegration
#     from sentry_sdk.integrations.logging import LoggingIntegration
    
#     sentry_logging = LoggingIntegration(
#         level=logging.INFO,
#         event_level=logging.ERROR
#     )
    
#     sentry_sdk.init(
#         dsn=SENTRY_DSN,
#         integrations=[DjangoIntegration(), sentry_logging],
#         traces_sample_rate=0.1,
#         send_default_pii=True
#     )