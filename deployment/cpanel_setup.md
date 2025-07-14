# AKILIMO Nigeria Association - cPanel Deployment Guide

This guide will help you deploy the AKILIMO Nigeria Association Django application to a cPanel hosting environment.

## Prerequisites

- cPanel hosting account with Python support
- MySQL database access
- SSH access (optional but recommended)
- Domain name configured

## Step 1: Prepare Your Local Environment

1. **Create production environment file:**
   ```bash
   cp .env.example .env
   ```

2. **Configure the .env file with production values:**
   ```bash
   # Django Settings
   SECRET_KEY=your-very-secure-secret-key-here
   DEBUG=False
   DJANGO_SETTINGS_MODULE=akilimo_nigeria.settings.production
   ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

   # Database Configuration
   DB_ENGINE=django.db.backends.mysql
   DB_NAME=your_cpanel_database_name
   DB_USER=your_cpanel_database_user
   DB_PASSWORD=your_cpanel_database_password
   DB_HOST=localhost
   DB_PORT=3306

   # Site Configuration
   SITE_URL=https://yourdomain.com
   
   # Email Configuration (use your hosting provider's SMTP)
   EMAIL_HOST=mail.yourdomain.com
   EMAIL_PORT=587
   EMAIL_USE_TLS=True
   EMAIL_HOST_USER=noreply@yourdomain.com
   EMAIL_HOST_PASSWORD=your-email-password
   
   # Security Settings
   SECURE_SSL_REDIRECT=True
   SESSION_COOKIE_SECURE=True
   CSRF_COOKIE_SECURE=True
   ```

## Step 2: Set Up Database in cPanel

1. **Create MySQL Database:**
   - Go to cPanel → MySQL Databases
   - Create a new database (e.g., `youruser_akilimo`)
   - Create a database user with full privileges
   - Note the database name, username, and password

2. **Update your .env file** with the database credentials

## Step 3: Upload Files to cPanel

### Option A: Using File Manager
1. Compress your project files into a ZIP
2. Upload via cPanel File Manager
3. Extract in your domain's directory

### Option B: Using Git (if available)
1. Clone the repository directly on the server
2. Configure the .env file on the server

### Option C: Using FTP/SFTP
1. Upload all project files except:
   - `venv/` (virtual environment)
   - `db.sqlite3` (development database)
   - `__pycache__/` directories
   - `.git/` (if using Git)

## Step 4: Set Up Python Environment

1. **Access Terminal/SSH** (if available) or use cPanel Python app

2. **Create virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

## Step 5: Configure Python App in cPanel

1. **Go to cPanel → Python App**

2. **Create New Application:**
   - Python version: 3.8+ (latest available)
   - Application root: `/public_html` (or your domain folder)
   - Application URL: `/` (or subdirectory if needed)
   - Application startup file: `akilimo_nigeria/wsgi.py`
   - Application Entry point: `application`

3. **Set Environment Variables:**
   Add all variables from your .env file in the cPanel Python app interface

## Step 6: Database Setup

1. **Run migrations:**
   ```bash
   python manage.py migrate
   ```

2. **Create cache table:**
   ```bash
   python manage.py createcachetable cache_table
   ```

3. **Create superuser:**
   ```bash
   python manage.py createsuperuser
   ```

4. **Collect static files:**
   ```bash
   python manage.py collectstatic
   ```

## Step 7: Configure Static Files

1. **In cPanel → File Manager**, ensure static files are in `/public_html/static/`

2. **Add to .htaccess** in your domain root:
   ```apache
   # Static files
   RewriteEngine On
   RewriteRule ^static/(.*)$ /static/$1 [L]
   RewriteRule ^media/(.*)$ /media/$1 [L]
   ```

## Step 8: SSL Certificate

1. **Enable SSL** in cPanel → SSL/TLS
2. **Update .env** to set `SECURE_SSL_REDIRECT=True`
3. **Restart the Python app**

## Step 9: Test the Deployment

1. **Visit your domain** to check if the site loads
2. **Test admin access** at `yourdomain.com/admin/`
3. **Check all functionality:**
   - User registration/login
   - Dashboard features
   - Payment processing (if configured)
   - Email sending

## Step 10: Post-Deployment Tasks

### Set Up Backups
1. **Database backups** via cPanel
2. **File backups** of media uploads
3. **Regular backup schedule**

### Configure Monitoring
1. **Error logging** (check Django logs)
2. **Uptime monitoring**
3. **Performance monitoring**

### Security Checklist
- [ ] SSL certificate installed and working
- [ ] Debug mode disabled (`DEBUG=False`)
- [ ] Secret key is unique and secure
- [ ] Database credentials are secure
- [ ] Admin URL is protected
- [ ] Regular security updates

## Troubleshooting

### Common Issues

1. **ImportError: No module named 'module_name'**
   - Ensure all dependencies are installed in the virtual environment
   - Check `requirements.txt` for missing packages

2. **Database connection errors**
   - Verify database credentials in .env
   - Check if database exists and user has proper permissions

3. **Static files not loading**
   - Run `python manage.py collectstatic`
   - Check static file paths in settings
   - Verify web server configuration

4. **500 Internal Server Error**
   - Check Django error logs
   - Verify all environment variables are set
   - Run `python manage.py check --deploy`

### Log Locations
- Django logs: `logs/akilimo_nigeria.log`
- Error logs: `logs/akilimo_nigeria_error.log`
- cPanel error logs: Check cPanel → Error Logs

## Maintenance Commands

```bash
# Update the application
git pull origin main  # if using Git
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput

# Restart the application
# Use cPanel Python app interface to restart

# Check application status
python manage.py check --deploy
```

## Support

If you encounter issues during deployment:

1. Check the error logs first
2. Verify all configuration settings
3. Test individual components (database, static files, etc.)
4. Contact your hosting provider for server-specific issues

## Security Notes

- Keep your `.env` file secure and never commit it to version control
- Regularly update dependencies for security patches
- Monitor access logs for suspicious activity
- Set up regular automated backups
- Use strong passwords for all accounts