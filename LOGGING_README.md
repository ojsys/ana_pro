# AKILIMO Nigeria Logging System

## Overview
The application now has comprehensive error logging configured to help track and debug issues.

## Log Files Location
All logs are stored in the `logs/` directory:

- **akilimo_nigeria.log** - General application logs (INFO level and above)
- **akilimo_nigeria_error.log** - Error logs only (ERROR level, with detailed stack traces)
- **akilimo_nigeria_debug.log** - Debug logs for dashboard app (DEBUG level)
- **akilimo_nigeria_db.log** - Database query logs (optional, controlled by DB_LOG_LEVEL)

## Log Levels
- **DEBUG** - Detailed information for diagnosing problems
- **INFO** - General informational messages
- **WARNING** - Warning messages
- **ERROR** - Error messages with stack traces
- **CRITICAL** - Critical errors that may cause system failure

## Quick Start

### View Logs (Easy Way)
Use the interactive log viewer script:
```bash
./view_logs.sh
```

This provides a menu with options to:
1. View error logs
2. View all logs
3. View debug logs
4. Monitor logs in real-time
5. Search logs
6. And more...

### View Logs (Manual Way)

**View latest errors:**
```bash
tail -n 50 logs/akilimo_nigeria_error.log
```

**Monitor errors in real-time:**
```bash
tail -f logs/akilimo_nigeria_error.log
```

**View all logs:**
```bash
tail -n 100 logs/akilimo_nigeria.log
```

**Search for specific error:**
```bash
grep -i "error_keyword" logs/akilimo_nigeria_error.log
```

**View logs from specific time:**
```bash
grep "2025-11-18 14:" logs/akilimo_nigeria_error.log
```

## What Gets Logged

### Automatic Logging
The system automatically logs:
- All Django errors (500 errors, exceptions)
- Request errors (404s, permission denied, etc.)
- Database errors
- Application errors in dashboard and website apps

### Error Details Include:
- Error type and message
- Full stack trace with file paths and line numbers
- User information (username, ID)
- Request details (method, path, GET/POST parameters)
- IP address
- User agent
- Timestamp

### Example Error Log Entry:
```
================================================================================
EXCEPTION OCCURRED
================================================================================
Error Type: DoesNotExist
Error Message: Membership matching query does not exist.

Request Information:
-------------------
User: john@example.com (ID: 123)
IP Address: 192.168.1.1
Method: GET
Path: /dashboard/membership/
GET Parameters: {}
POST Parameters: {}

User Agent: Mozilla/5.0...
Referer: /dashboard/

Stack Trace:
------------
Traceback (most recent call last):
  File "/path/to/views.py", line 123, in view_name
    membership = Membership.objects.get(member=request.user)
dashboard.models.DoesNotExist: Membership matching query does not exist.
================================================================================
```

## Configuration

### Environment Variables
Add these to your `.env` file to customize logging:

```bash
# Log file paths (optional, defaults shown)
LOG_FILE=/path/to/logs/akilimo_nigeria.log
ERROR_LOG_FILE=/path/to/logs/akilimo_nigeria_error.log
DEBUG_LOG_FILE=/path/to/logs/akilimo_nigeria_debug.log
DB_LOG_FILE=/path/to/logs/akilimo_nigeria_db.log

# Database query logging level (INFO or DEBUG)
DB_LOG_LEVEL=INFO

# Enable request logging (logs every HTTP request)
LOG_ALL_REQUESTS=False  # Set to True to enable
```

### Enable Request Logging
To log every incoming request (useful for debugging but verbose):
```bash
# In .env
LOG_ALL_REQUESTS=True
```

This will log:
```
INFO Request: GET /dashboard/ | User: john | IP: 192.168.1.1
INFO Response: GET /dashboard/ | Status: 200
```

## Log Rotation
Logs automatically rotate to prevent disk space issues:
- **Error logs**: 15MB per file, keeps 10 backups
- **General logs**: 15MB per file, keeps 10 backups
- **Debug logs**: 20MB per file, keeps 5 backups
- **DB logs**: 10MB per file, keeps 5 backups

Old logs are automatically renamed with `.1`, `.2`, etc. suffixes.

## Production Deployment

### On Production Server
1. Ensure logs directory exists:
```bash
mkdir -p /path/to/project/logs
chmod 755 /path/to/project/logs
```

2. Make sure web server has write permissions:
```bash
chown -R www-data:www-data /path/to/project/logs  # For Apache/Nginx
```

3. Copy view_logs.sh to server:
```bash
scp view_logs.sh user@server:/path/to/project/
ssh user@server "chmod +x /path/to/project/view_logs.sh"
```

4. View logs on server:
```bash
ssh user@server
cd /path/to/project
./view_logs.sh
```

### Email Notifications
Critical errors are automatically emailed to ADMINS when DEBUG=False:

```python
# In production settings
ADMINS = [
    ('Admin Name', 'admin@example.com'),
]
```

## Troubleshooting

### Logs not being created
1. Check directory permissions:
```bash
ls -la logs/
```

2. Check Django can write to directory:
```bash
touch logs/test.log
rm logs/test.log
```

3. Verify middleware is loaded:
```python
# In settings/base.py
MIDDLEWARE = [
    ...
    'dashboard.middleware.ErrorLoggingMiddleware',
    ...
]
```

### Logs are empty
1. Trigger a test error:
```python
# Add to a view temporarily
raise Exception("Test error for logging")
```

2. Check log level settings in production.py

3. Verify you're checking the right environment (dev vs production)

## Best Practices

1. **Regular Monitoring**: Check error logs daily in production
2. **Search Before Fixing**: Search logs for error patterns before debugging
3. **Keep Rotations**: Don't delete old log files immediately, they help identify patterns
4. **Sensitive Data**: The middleware automatically redacts passwords and tokens
5. **Production Only**: Keep DB_LOG_LEVEL at INFO in production to avoid huge log files

## Log Analysis

### Find most common errors:
```bash
grep "Error Type:" logs/akilimo_nigeria_error.log | sort | uniq -c | sort -rn
```

### Count errors per hour:
```bash
grep "ERROR" logs/akilimo_nigeria.log | cut -d' ' -f2 | cut -d: -f1 | sort | uniq -c
```

### Find errors from specific user:
```bash
grep "User: username" logs/akilimo_nigeria_error.log -A 20
```

## Support
For issues with logging, check:
1. Django documentation: https://docs.djangoproject.com/en/stable/topics/logging/
2. Python logging: https://docs.python.org/3/library/logging.html
