# Production Logging Setup Guide

## Server Information
- **Server Path**: `/home/akilimon/ana_pro/`
- **Logs Directory**: `/home/akilimon/ana_pro/logs/`

## Step-by-Step Setup

### 1. SSH into the Production Server
```bash
ssh akilimon@akilimonigeria.org
# Or use your hosting panel's terminal
```

### 2. Navigate to Project Directory
```bash
cd /home/akilimon/ana_pro
```

### 3. Create Logs Directory
```bash
mkdir -p logs
```

### 4. Set Proper Permissions
```bash
# Make sure the web server can write to logs directory
chmod 755 logs

# If using Apache/Passenger, ensure correct ownership
# (adjust based on your server configuration)
chown -R akilimon:akilimon logs

# Or if your web server runs as a different user (e.g., www-data, apache, nobody)
# chown -R www-data:www-data logs
```

### 5. Create .gitignore in Logs Directory
```bash
cat > logs/.gitignore << 'EOF'
# Ignore all log files
*.log
*.log.*

# But keep this directory in git
!.gitignore
EOF
```

### 6. Test Log Creation
```bash
# Test if logs can be created
touch logs/test.log
ls -la logs/

# If successful, remove test file
rm logs/test.log
```

### 7. Deploy Updated Code
```bash
# Pull latest changes
git pull origin main

# Or upload files via FTP/SFTP
# Make sure to include:
# - akilimo_nigeria/settings/production.py (updated)
# - dashboard/middleware.py (new)
# - akilimo_nigeria/settings/base.py (updated MIDDLEWARE)
```

### 8. Restart Web Server/Application
```bash
# For Passenger (common on shared hosting)
touch tmp/restart.txt

# For systemd/gunicorn
sudo systemctl restart gunicorn
# or
sudo systemctl restart your-app-name

# For Apache
sudo service apache2 restart

# For cPanel
# Use "Restart Application" button in cPanel
```

### 9. Verify Logs Are Being Created
```bash
# Generate a test request
curl https://akilimonigeria.org/dashboard/

# Check if log files were created
ls -lh logs/

# View the general log
tail -n 20 logs/akilimo_nigeria.log
```

### 10. Monitor Error Logs
```bash
# Watch for errors in real-time
tail -f logs/akilimo_nigeria_error.log

# Or use the interactive viewer (if uploaded)
./view_logs.sh
```

## Troubleshooting

### Logs Not Being Created?

**Check 1: Directory Permissions**
```bash
ls -la logs/
# Should show: drwxr-xr-x (755)
```

**Check 2: Web Server User**
```bash
# Find out which user runs your web application
ps aux | grep -E 'apache|nginx|passenger|python'

# Ensure that user can write to logs
sudo -u www-data touch logs/test.log
# (replace www-data with your actual web server user)
```

**Check 3: SELinux (if enabled)**
```bash
# Check if SELinux is blocking writes
getenforce

# If Enforcing, allow writes to logs
sudo chcon -R -t httpd_log_t logs/
```

**Check 4: Disk Space**
```bash
# Check available disk space
df -h

# Check quota (on shared hosting)
quota -s
```

### Permission Denied Errors?

**Option 1: Change ownership to web server user**
```bash
sudo chown -R www-data:www-data logs/
# Replace www-data with your web server user
```

**Option 2: Use group permissions**
```bash
# Add your user to web server group
sudo usermod -a -G www-data akilimon

# Set group write permissions
chmod 775 logs/
```

**Option 3: For shared hosting (cPanel)**
```bash
# Usually the user and web server are the same
chmod 755 logs/
chown -R akilimon:akilimon logs/
```

### Logs Are Empty?

1. **Check Django Settings Module**
```bash
echo $DJANGO_SETTINGS_MODULE
# Should be: akilimo_nigeria.settings.production
```

2. **Check if middleware is loaded**
```bash
# In Django shell
python manage.py shell
>>> from django.conf import settings
>>> 'dashboard.middleware.ErrorLoggingMiddleware' in settings.MIDDLEWARE
True
```

3. **Manually trigger an error**
```bash
# Add this temporarily to a view:
raise Exception("Test error for logging")
```

## Quick Commands for Production

### View Latest Errors
```bash
tail -n 50 /home/akilimon/ana_pro/logs/akilimo_nigeria_error.log
```

### Monitor Errors Live
```bash
tail -f /home/akilimon/ana_pro/logs/akilimo_nigeria_error.log
```

### Search for Specific Error
```bash
grep -i "DoesNotExist" /home/akilimon/ana_pro/logs/akilimo_nigeria_error.log
```

### Check Log Sizes
```bash
du -h /home/akilimon/ana_pro/logs/*.log
```

### Download Logs to Local Machine
```bash
# From your local machine
scp akilimon@akilimonigeria.org:/home/akilimon/ana_pro/logs/akilimo_nigeria_error.log ./

# Or download all logs
scp -r akilimon@akilimonigeria.org:/home/akilimon/ana_pro/logs/ ./logs_backup/
```

## Maintenance

### Weekly Tasks
- Check error log for recurring issues
- Monitor log file sizes

### Monthly Tasks
- Review and archive old rotated logs
- Check disk space usage

### As Needed
- Download logs before major deployments
- Clear old logs if disk space is low

## Log Retention

Logs are automatically rotated:
- When files reach their size limit (10-20MB)
- Old logs are renamed with .1, .2, etc.
- System keeps 5-10 backup copies
- Oldest logs are automatically deleted

Total disk usage: ~200-300MB maximum

## Support

If you encounter issues:
1. Check this guide
2. Review error messages in logs
3. Check server error logs: `/var/log/apache2/error.log` or `/var/log/nginx/error.log`
4. Contact hosting support if permissions can't be set

## Security Note

Log files may contain sensitive information. Ensure:
- Logs directory is not publicly accessible via web
- Don't commit .log files to git (already in .gitignore)
- Passwords and tokens are automatically redacted by middleware
- Consider encrypting logs for highly sensitive applications
