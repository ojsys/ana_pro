# AKILIMO Nigeria Association - Deployment Checklist

Use this checklist to ensure a successful deployment to production.

## Pre-Deployment Checklist

### Code Preparation
- [ ] All features tested in development environment
- [ ] Code reviewed and approved
- [ ] Git repository is up to date
- [ ] No debug code or console.log statements left in production code
- [ ] All TODO comments addressed or documented

### Settings and Configuration
- [ ] `.env.example` file is up to date with all required variables
- [ ] Production `.env` file created and configured
- [ ] `SECRET_KEY` is unique and secure (not the default one)
- [ ] `DEBUG=False` in production settings
- [ ] `ALLOWED_HOSTS` configured with production domain(s)
- [ ] Database settings configured for production MySQL
- [ ] Email settings configured with hosting provider's SMTP
- [ ] Security settings enabled (SSL redirect, secure cookies)
- [ ] CORS settings configured for production domains only

### Dependencies and Requirements
- [ ] `requirements.txt` is up to date
- [ ] All production dependencies included
- [ ] No development-only packages in production requirements
- [ ] Dependencies tested in production-like environment

### Database Preparation
- [ ] Production database created in cPanel
- [ ] Database user created with appropriate permissions
- [ ] Database connection tested
- [ ] Migration files reviewed and tested
- [ ] Data seeding planned (if needed)

## Deployment Process

### File Upload
- [ ] Project files uploaded to server (excluding venv, .git, __pycache__)
- [ ] `.env` file uploaded and configured on server
- [ ] File permissions set correctly
- [ ] Directory structure verified

### Python Environment Setup
- [ ] Virtual environment created on server
- [ ] Python version verified (3.8+)
- [ ] Dependencies installed from requirements.txt
- [ ] Django installation verified

### cPanel Configuration
- [ ] Python app created in cPanel
- [ ] Application root path set correctly
- [ ] WSGI application entry point configured
- [ ] Environment variables set in cPanel Python app
- [ ] Application started successfully

### Database Setup
- [ ] Database migrations run successfully
- [ ] Cache table created (if using database cache)
- [ ] Test data loaded (if needed)
- [ ] Database connection verified from Django

### Static Files and Media
- [ ] Static files collected (`collectstatic` run)
- [ ] Static files directory accessible via web server
- [ ] Media files directory created and writable
- [ ] Static file serving configured
- [ ] CSS and JavaScript files loading correctly

### SSL and Security
- [ ] SSL certificate installed and working
- [ ] HTTP to HTTPS redirect working
- [ ] Security headers configured
- [ ] Admin interface accessible and secure
- [ ] Session security working correctly

## Post-Deployment Testing

### Basic Functionality
- [ ] Homepage loads correctly
- [ ] User registration works
- [ ] User login/logout works
- [ ] Dashboard accessible for logged-in users
- [ ] Admin interface accessible

### Dashboard Features
- [ ] Dashboard statistics display correctly with comma formatting
- [ ] Partner organizations data loads
- [ ] Extension agents data accurate
- [ ] Geographic areas and cities data correct
- [ ] Charts and visualizations working

### Admin Interface
- [ ] All models accessible in admin
- [ ] Filters working correctly
- [ ] Search functionality working
- [ ] Add/edit/delete operations working
- [ ] Pagination working for large datasets

### API and External Services
- [ ] EiA MELIA API integration working (if configured)
- [ ] Paystack payment integration working (if configured)
- [ ] Email sending working
- [ ] External API calls successful

### Performance and Error Handling
- [ ] Page load times acceptable
- [ ] Error pages (404, 500) display correctly
- [ ] Error logging working
- [ ] No broken links or missing images

## Production Monitoring Setup

### Logging and Monitoring
- [ ] Django error logging configured
- [ ] Log files rotating properly
- [ ] Error notification emails working
- [ ] Application monitoring set up
- [ ] Uptime monitoring configured

### Backups
- [ ] Database backup schedule configured
- [ ] Media files backup plan in place
- [ ] Backup restoration tested
- [ ] Backup storage secure and accessible

### Security Monitoring
- [ ] Access logs being monitored
- [ ] Security updates plan in place
- [ ] Admin access restricted to authorized users only
- [ ] Regular security audit scheduled

## Go-Live Checklist

### Final Verification
- [ ] All functionality tested end-to-end
- [ ] Performance acceptable under load
- [ ] Mobile responsiveness verified
- [ ] Cross-browser compatibility checked
- [ ] SEO settings configured

### DNS and Domain
- [ ] Domain DNS pointing to correct server
- [ ] WWW and non-WWW redirects working
- [ ] SSL certificate valid for all domain variants
- [ ] Email DNS records configured (if using custom email)

### Communication
- [ ] Stakeholders notified of go-live
- [ ] Support team briefed on new deployment
- [ ] Documentation updated with production URLs
- [ ] User guides updated (if needed)

## Post-Go-Live Tasks

### First 24 Hours
- [ ] Monitor error logs closely
- [ ] Check performance metrics
- [ ] Monitor user activity and registrations
- [ ] Verify all scheduled tasks working
- [ ] Confirm email delivery working

### First Week
- [ ] Review server resource usage
- [ ] Check backup completion
- [ ] Monitor uptime and availability
- [ ] Review user feedback
- [ ] Address any performance issues

### Ongoing Maintenance
- [ ] Schedule regular updates
- [ ] Plan security patches
- [ ] Monitor database growth
- [ ] Review and optimize performance
- [ ] Update documentation as needed

## Emergency Procedures

### Rollback Plan
- [ ] Previous version backup ready
- [ ] Database rollback procedure documented
- [ ] Rollback testing completed
- [ ] Emergency contact list prepared

### Incident Response
- [ ] Error escalation process defined
- [ ] Emergency contacts available
- [ ] Incident documentation process ready
- [ ] Communication plan for outages

## Sign-off

### Technical Team
- [ ] Developer: _________________ Date: _______
- [ ] DevOps/Admin: _____________ Date: _______
- [ ] QA Tester: _______________ Date: _______

### Business Team
- [ ] Project Manager: __________ Date: _______
- [ ] Stakeholder: _____________ Date: _______

### Final Approval
- [ ] Production deployment approved
- [ ] Go-live date confirmed: _______________
- [ ] Support procedures in place

---

**Notes:**
- Complete each item before proceeding to the next section
- Document any issues or deviations from the standard process
- Keep this checklist for future deployments and continuous improvement