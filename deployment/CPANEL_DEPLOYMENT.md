# AKILIMO Nigeria Association - cPanel Deployment Guide

## ✅ **cPanel Compatibility Confirmed**

This application is **fully compatible** with cPanel hosting. Here's what has been optimized for cPanel:

### **Key cPanel Optimizations:**

1. **✅ PyMySQL Database Driver** - Pure Python, no compilation needed
2. **✅ passenger_wsgi.py** - cPanel Python app entry point
3. **✅ Static Files Handling** - Configured for cPanel's file structure
4. **✅ Environment Variables** - Simplified for cPanel interface
5. **✅ File Permissions** - Proper structure for shared hosting

---

## **Step-by-Step cPanel Deployment**

### **Prerequisites**
- cPanel hosting with Python 3.8+ support
- MySQL database access
- Domain/subdomain configured
- File Manager or FTP access

---

## **Phase 1: cPanel Preparation**

### **1.1 Create MySQL Database**
1. Go to **cPanel → MySQL Databases**
2. Create database: `youruser_akilimo`
3. Create user: `youruser_akilimo`
4. Grant ALL PRIVILEGES to user
5. **Note the exact names** (they'll have your cPanel username prefix)

### **1.2 Create Python App**
1. Go to **cPanel → Python Selector** or **Setup Python App**
2. Click **Create Application**
3. **Settings:**
   - **Python Version**: 3.8+ (latest available)
   - **Application Root**: `public_html` (or `public_html/app` for subdomain)
   - **Application URL**: `/` (for main domain) or `/app` (for subdirectory)
   - **Application startup file**: `passenger_wsgi.py`
   - **Application Entry point**: `application`

### **1.3 Note Important Paths**
After creating the app, note these paths:
- **Application Root**: `/home/yourusername/public_html/`
- **Virtual Environment**: `/home/yourusername/virtualenv/public_html/3.x/`
- **Static Files Path**: `/home/yourusername/public_html/static/`

---

## **Phase 2: File Upload**

### **2.1 Upload Application Files**
**Via File Manager:**
1. Compress your project locally (exclude: `venv/`, `db.sqlite3`, `__pycache__/`)
2. Upload ZIP to your application root
3. Extract files

**Via FTP:**
1. Upload all files to application root
2. Ensure `passenger_wsgi.py` is in the root directory

### **2.2 Set File Permissions**
Ensure these permissions:
- **Directories**: 755
- **Python files**: 644
- **passenger_wsgi.py**: 644
- **logs/ directory**: 755 (create if needed)

---

## **Phase 3: Environment Configuration**

### **3.1 Create .env File**
In your application root, create `.env` with:

```bash
# Django Settings
SECRET_KEY=your-super-secret-production-key-here-make-it-very-long
DEBUG=False
DJANGO_SETTINGS_MODULE=akilimo_nigeria.settings.production

# Domain Configuration
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
SITE_URL=https://yourdomain.com

# cPanel Hosting Flag
CPANEL_HOSTING=True

# Database Configuration (replace with your actual details)
DB_ENGINE=django.db.backends.mysql
DB_NAME=youruser_akilimo
DB_USER=youruser_akilimo
DB_PASSWORD=your_database_password
DB_HOST=localhost
DB_PORT=3306

# File Paths (replace 'yourusername' with actual cPanel username)
STATIC_ROOT=/home/yourusername/public_html/static/
MEDIA_ROOT=/home/yourusername/public_html/media/
STATIC_URL=/static/
MEDIA_URL=/media/

# Email Configuration (use your hosting provider's SMTP)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=mail.yourdomain.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=noreply@yourdomain.com
EMAIL_HOST_PASSWORD=your_email_password
DEFAULT_FROM_EMAIL=noreply@yourdomain.com

# Admin Configuration
ADMIN_NAME=Your Name
ADMIN_EMAIL=admin@yourdomain.com

# API Keys (optional - configure if needed)
EIA_MELIA_API_TOKEN=your_api_token_if_needed
PAYSTACK_PUBLIC_KEY=pk_live_your_key_if_needed
PAYSTACK_SECRET_KEY=sk_live_your_key_if_needed

# Security Settings
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
SECURE_HSTS_SECONDS=31536000

# Logging
LOG_FILE=/home/yourusername/public_html/logs/akilimo.log
ERROR_LOG_FILE=/home/yourusername/public_html/logs/akilimo_error.log
```

### **3.2 Secure the .env File**
Add to `.htaccess` in application root:
```apache
<Files ".env">
    Order allow,deny
    Deny from all
</Files>
```

---

## **Phase 4: Python Environment Setup**

### **4.1 Access Terminal**
- **Option A**: cPanel Terminal (if available)
- **Option B**: SSH (if enabled)
- **Option C**: cPanel Python App interface

### **4.2 Activate Virtual Environment**
```bash
source /home/yourusername/virtualenv/public_html/3.x/bin/activate
```

### **4.3 Install Dependencies**
```bash
cd /home/yourusername/public_html
pip install --upgrade pip
pip install -r requirements.txt
```

**Note**: If you get permission errors, contact your hosting provider.

---

## **Phase 5: Django Setup**

### **5.1 Database Setup**
```bash
python manage.py migrate
python manage.py createcachetable cache_table
```

### **5.2 Create Superuser**
```bash
python manage.py createsuperuser
```

### **5.3 Collect Static Files**
```bash
python manage.py collectstatic --noinput
```

### **5.4 Test Configuration**
```bash
python manage.py check --deploy
```

---

## **Phase 6: Web Server Configuration**

### **6.1 Configure Static Files**
Create/edit `.htaccess` in `public_html`:
```apache
# Static and Media Files
RewriteEngine On

# Handle static files
RewriteRule ^static/(.*)$ /static/$1 [L]
RewriteRule ^media/(.*)$ /media/$1 [L]

# Security headers
Header always set X-Content-Type-Options nosniff
Header always set X-Frame-Options DENY
Header always set X-XSS-Protection "1; mode=block"

# Cache static files
<FilesMatch "\.(css|js|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$">
    ExpiresActive On
    ExpiresDefault "access plus 1 month"
    Header set Cache-Control "public, immutable, max-age=2592000"
</FilesMatch>

# Protect sensitive files
<Files ".env">
    Order allow,deny
    Deny from all
</Files>

<Files "*.py">
    Order allow,deny
    Deny from all
</Files>
```

### **6.2 Restart Python App**
In cPanel → Python App → Click **Restart**

---

## **Phase 7: Testing**

### **7.1 Basic Tests**
1. **Visit your domain** - Should show homepage
2. **Check admin**: `yourdomain.com/admin/`
3. **Test static files**: CSS/JS should load
4. **Test database**: Login should work

### **7.2 Dashboard Tests**
1. **View dashboard** after login
2. **Check statistics** - Should show formatted numbers:
   - Extension Agents: **1,040**
   - Cities Reached: **4,897**
   - Partner Organizations: **145**
3. **Test admin interface** - All filters should work

---

## **Common cPanel Issues & Solutions**

### **Issue 1: Import Errors**
```
ImportError: No module named 'module_name'
```
**Solution:**
- Ensure virtual environment is activated
- Reinstall requirements: `pip install -r requirements.txt`
- Check Python version compatibility

### **Issue 2: Database Connection Errors**
```
django.db.utils.OperationalError: (2003, "Can't connect to MySQL server")
```
**Solution:**
- Verify database name includes cPanel username prefix
- Check database user permissions
- Confirm database credentials in .env

### **Issue 3: Static Files Not Loading**
**Solution:**
- Run `python manage.py collectstatic`
- Check STATIC_ROOT path in .env
- Verify .htaccess rules
- Check file permissions (755 for directories, 644 for files)

### **Issue 4: Permission Denied Errors**
**Solution:**
- Check file permissions
- Ensure application directory is writable
- Contact hosting provider for permission issues

### **Issue 5: 500 Internal Server Error**
**Solution:**
- Check cPanel Error Logs
- Verify .env file configuration
- Run `python manage.py check --deploy`
- Ensure passenger_wsgi.py is in correct location

---

## **Performance Optimization for cPanel**

### **Database Optimization**
- Use database connection pooling
- Regular database maintenance
- Index optimization for large datasets

### **Static Files**
- Enable browser caching via .htaccess
- Compress images and assets
- Use CDN if available

### **Application Optimization**
- Enable Django caching
- Optimize database queries
- Use pagination for large datasets

---

## **Maintenance Tasks**

### **Regular Updates**
```bash
# Backup database first
python manage.py dumpdata > backup_$(date +%Y%m%d).json

# Update application
git pull  # if using git
pip install -r requirements.txt --upgrade
python manage.py migrate
python manage.py collectstatic --noinput

# Restart app in cPanel
```

### **Monitoring**
- Check error logs regularly
- Monitor disk space usage
- Review database performance
- Track user activity

---

## **Security Checklist for cPanel**

- [ ] `.env` file protected via .htaccess
- [ ] DEBUG=False in production
- [ ] Strong SECRET_KEY configured
- [ ] SSL certificate installed
- [ ] Security headers configured
- [ ] Regular backups scheduled
- [ ] Admin access restricted
- [ ] Error logging enabled

---

## **Support**

**For cPanel-specific issues:**
1. Check cPanel Error Logs first
2. Review this deployment guide
3. Test individual components
4. Contact your hosting provider

**For application issues:**
1. Check Django logs
2. Verify configuration
3. Test in development environment

---

## **Success Indicators**

✅ **Your deployment is successful when:**
- Homepage loads without errors
- Admin interface accessible
- Dashboard shows formatted numbers (1,040, 4,897, etc.)
- User registration/login works
- Static files (CSS/JS) load correctly
- Database operations work
- SSL certificate active

**🎉 Your AKILIMO Nigeria Association app is now live on cPanel!**