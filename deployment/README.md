# AKILIMO Nigeria Association - Production Deployment

This directory contains all the necessary files and documentation for deploying the AKILIMO Nigeria Association Django application to a cPanel production environment.

## Files in this Directory

### 📋 Documentation
- **`cpanel_setup.md`** - Complete step-by-step guide for cPanel deployment
- **`DEPLOYMENT_CHECKLIST.md`** - Comprehensive checklist to ensure successful deployment
- **`README.md`** - This file, overview of deployment resources

### 🚀 Scripts
- **`deploy.sh`** - Automated deployment script for production setup

## Quick Start

1. **Read the documentation first:**
   ```bash
   # Start with the cPanel setup guide
   cat cpanel_setup.md
   
   # Use the checklist to track progress
   cat DEPLOYMENT_CHECKLIST.md
   ```

2. **Prepare your environment:**
   ```bash
   # Copy environment template
   cp ../.env.example ../.env
   
   # Edit with your production values
   nano ../.env
   ```

3. **Run the deployment script:**
   ```bash
   # Make sure you're in the project root
   cd ..
   
   # Run the deployment script
   ./deployment/deploy.sh
   ```

## Environment Separation

The application is configured with separate settings for different environments:

### Development
- **Settings Module:** `akilimo_nigeria.settings.development`
- **Database:** SQLite (db.sqlite3)
- **Debug:** Enabled
- **Security:** Relaxed for development

### Production
- **Settings Module:** `akilimo_nigeria.settings.production`
- **Database:** MySQL (configured via environment variables)
- **Debug:** Disabled
- **Security:** Hardened for production

## Key Configuration Files

### Settings Structure
```
akilimo_nigeria/settings/
├── __init__.py
├── base.py          # Common settings
├── development.py   # Development-specific settings
└── production.py    # Production-specific settings
```

### Environment Variables
The application uses python-decouple for environment variable management:
- **Development:** Uses defaults suitable for local development
- **Production:** Requires explicit configuration of all variables

## Security Features

### Production Security Measures
- ✅ Debug mode disabled
- ✅ Secure secret key required
- ✅ HTTPS enforcement (configurable)
- ✅ Secure cookies
- ✅ HSTS headers
- ✅ XSS protection
- ✅ Content type sniffing protection
- ✅ CSRF protection

### Security Checklist
- [ ] Change default SECRET_KEY
- [ ] Configure ALLOWED_HOSTS
- [ ] Enable SSL/HTTPS
- [ ] Set secure cookie flags
- [ ] Configure proper CORS settings
- [ ] Set up error monitoring
- [ ] Configure log rotation

## Database Configuration

### Development
Uses SQLite for easy setup and testing.

### Production
Supports MySQL with the following configuration options:

1. **DATABASE_URL method (recommended):**
   ```
   DATABASE_URL=mysql://user:password@host:port/database
   ```

2. **Individual settings method:**
   ```
   DB_ENGINE=django.db.backends.mysql
   DB_NAME=your_database
   DB_USER=your_user
   DB_PASSWORD=your_password
   DB_HOST=localhost
   DB_PORT=3306
   ```

## Static Files Handling

### Development
Django serves static files automatically when DEBUG=True.

### Production
Uses WhiteNoise middleware for efficient static file serving:
- Automatic compression
- Cache headers
- Efficient serving without web server configuration

## Logging Configuration

### Development
- Console output for immediate feedback
- Debug level logging
- File logging for persistent records

### Production
- Rotating file logs to prevent disk space issues
- Error-level logging to separate file
- Email notifications for critical errors
- Performance optimized logging levels

## Performance Considerations

### Caching
- **Development:** Local memory cache
- **Production:** Database cache (Redis optional)

### Database Optimizations
- Connection pooling
- Query optimization
- Proper indexing

### Static Files
- Compression enabled
- Browser caching headers
- CDN ready (if needed)

## Backup Strategy

### Database Backups
- Daily automated backups via cPanel
- Weekly full backups
- Monthly archive backups

### File Backups
- Media files backup
- Application code backup
- Configuration backup

## Monitoring and Maintenance

### Health Checks
- Application status monitoring
- Database connectivity checks
- External API availability

### Updates
- Security patches
- Dependency updates
- Feature releases

### Performance Monitoring
- Response time tracking
- Error rate monitoring
- Resource usage monitoring

## Troubleshooting

### Common Issues
1. **Import errors** - Check virtual environment and dependencies
2. **Database connection** - Verify credentials and permissions
3. **Static files not loading** - Run collectstatic and check paths
4. **500 errors** - Check Django logs and settings

### Log Locations
- Application logs: `logs/akilimo_nigeria.log`
- Error logs: `logs/akilimo_nigeria_error.log`
- cPanel logs: Available in cPanel → Error Logs

### Debug Steps
1. Check environment variables
2. Verify database connection
3. Test static file serving
4. Review error logs
5. Run Django checks: `python manage.py check --deploy`

## Support

For deployment issues:
1. Check the troubleshooting section
2. Review error logs
3. Verify configuration against checklist
4. Contact hosting provider for server-specific issues

## Version History

- **v1.0** - Initial production deployment setup
- Includes dashboard with comma-formatted numbers
- Partner organization management
- Custom admin interface
- Payment integration ready

---

**Remember:** Always test deployments in a staging environment before production!