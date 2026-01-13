# Automatic Data Sync Guide
## Akilimo Nigeria Association - EiA MELIA API Integration

This guide explains how to set up and manage automatic data synchronization from the EiA MELIA API to keep your dashboard statistics up-to-date.

---

## Table of Contents
1. [Overview](#overview)
2. [Quick Setup](#quick-setup)
3. [Manual Setup](#manual-setup)
4. [Testing](#testing)
5. [Monitoring](#monitoring)
6. [Troubleshooting](#troubleshooting)
7. [Advanced Configuration](#advanced-configuration)

---

## Overview

The automatic sync system fetches participant data from the EiA MELIA API every **6 hours** to ensure your dashboard and homepage statistics are always current.

### What Gets Synced:
- Farmer/participant records
- Geographic data (states, cities)
- Partner organizations
- Training events
- Gender and demographic information
- All fields from the AkilimoParticipant model

### Sync Schedule:
- **Frequency**: Every 6 hours
- **Times**: 12:00 AM, 6:00 AM, 12:00 PM, 6:00 PM (daily)
- **Method**: Automated via cron job

---

## Quick Setup

### Automatic Setup (Recommended)

Run the setup script to configure everything automatically:

```bash
cd /Users/Apple/projects/ana_pro
./setup_auto_sync.sh
```

This script will:
1. Create the sync execution script (`run_sync.sh`)
2. Set up the logs directory
3. Offer to add the cron job automatically
4. Display next steps and testing commands

**That's it!** Your automatic sync is now configured.

---

## Manual Setup

If you prefer to set up manually or need custom configuration:

### Step 1: Create Sync Script

Create a file named `run_sync.sh` in your project root:

```bash
#!/bin/bash
# Automated sync script for Akilimo data

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Activate virtual environment
source venv/bin/activate

# Set Django settings module
export DJANGO_SETTINGS_MODULE=akilimo_nigeria.settings

# Run the sync command
python manage.py sync_akilimo_data --batch-size=1000 >> logs/sync.log 2>&1

# Log completion
echo "Sync completed at $(date)" >> logs/sync.log
```

Make it executable:
```bash
chmod +x run_sync.sh
```

### Step 2: Create Logs Directory

```bash
mkdir -p logs
```

### Step 3: Add Cron Job

Open crontab editor:
```bash
crontab -e
```

Add this line (sync every 6 hours):
```cron
0 */6 * * * /Users/Apple/projects/ana_pro/run_sync.sh
```

Save and exit. Verify the cron job:
```bash
crontab -l
```

---

## Testing

### Test Manual Sync

Before relying on automatic sync, test it manually:

```bash
# Activate virtual environment
source venv/bin/activate

# Run sync command with dry-run to preview
python manage.py sync_akilimo_data --dry-run

# Run actual sync
python manage.py sync_akilimo_data

# Run sync with specific batch size
python manage.py sync_akilimo_data --batch-size=500

# Force update existing records
python manage.py sync_akilimo_data --force
```

### Test the Sync Script

```bash
./run_sync.sh
```

Check the logs:
```bash
tail -f logs/sync.log
```

### Verify Data in Database

```bash
source venv/bin/activate
python manage.py shell
```

Then in the Python shell:
```python
from dashboard.models import AkilimoParticipant, DataSyncLog

# Check total records
print(f"Total participants: {AkilimoParticipant.objects.count()}")

# Check recent sync logs
recent_syncs = DataSyncLog.objects.order_by('-started_at')[:5]
for sync in recent_syncs:
    print(f"{sync.started_at}: {sync.status} - {sync.records_created} created, {sync.records_updated} updated")

# Check data from Nigeria
nigeria_count = AkilimoParticipant.objects.filter(country__iexact='nigeria').count()
print(f"Nigeria participants: {nigeria_count}")
```

---

## Monitoring

### View Sync Logs

Real-time monitoring:
```bash
tail -f logs/sync.log
```

View last 50 lines:
```bash
tail -50 logs/sync.log
```

Search for errors:
```bash
grep -i error logs/sync.log
```

### Check Cron Job Status

List all cron jobs:
```bash
crontab -l
```

View cron execution logs (macOS):
```bash
log show --predicate 'process == "cron"' --last 1d
```

View cron execution logs (Linux):
```bash
grep CRON /var/log/syslog | tail -20
```

### Monitor via Django Admin

1. Log in to Django admin: `http://your-domain.com/admin/`
2. Navigate to **Dashboard > Data Sync Logs**
3. View sync history, success rates, and error details

---

## Troubleshooting

### Sync Not Running

**Check if cron job exists:**
```bash
crontab -l | grep sync
```

**Check cron daemon (macOS):**
```bash
sudo launchctl list | grep cron
```

**Check cron service (Linux):**
```bash
sudo systemctl status cron
```

### Permission Issues

Make scripts executable:
```bash
chmod +x run_sync.sh
chmod +x setup_auto_sync.sh
```

Ensure virtual environment is accessible:
```bash
ls -la venv/bin/activate
```

### API Token Issues

Verify API configuration in Django admin:
1. Go to **Dashboard > API Configurations**
2. Ensure an active configuration exists with a valid token
3. Test the token manually:

```bash
source venv/bin/activate
python manage.py shell
```

```python
from dashboard.models import APIConfiguration
from dashboard.services import EiAMeliaAPIService

config = APIConfiguration.objects.filter(is_active=True).first()
if config:
    api = EiAMeliaAPIService(config.token)
    result = api.get_participants_by_usecase('akilimo', page=1, page_size=1)
    print(f"API Test: {result.get('count', 0)} total records available")
else:
    print("No active API configuration found!")
```

### Database Connection Issues

Check database settings in `.env`:
```bash
cat .env | grep DATABASE
```

Test database connection:
```bash
source venv/bin/activate
python manage.py dbshell
```

### Large Dataset Issues

If syncing takes too long or times out:

**Option 1: Reduce batch size**
```bash
python manage.py sync_akilimo_data --batch-size=500
```

**Option 2: Limit total records (for testing)**
```bash
python manage.py sync_akilimo_data --max-records=5000
```

**Option 3: Use incremental sync (sync only new records)**
```bash
python manage.py sync_akilimo_data  # Without --force flag
```

---

## Advanced Configuration

### Change Sync Frequency

Edit your crontab:
```bash
crontab -e
```

Common cron schedules:

| Frequency | Cron Expression | Description |
|-----------|----------------|-------------|
| Every hour | `0 * * * *` | At minute 0 of every hour |
| Every 3 hours | `0 */3 * * *` | At minute 0 of every 3rd hour |
| Every 6 hours | `0 */6 * * *` | At minute 0 of every 6th hour (default) |
| Every 12 hours | `0 */12 * * *` | At 12:00 AM and 12:00 PM |
| Daily at 2 AM | `0 2 * * *` | Every day at 2:00 AM |
| Twice daily | `0 6,18 * * *` | At 6:00 AM and 6:00 PM |

### Email Notifications on Sync Failure

Modify `run_sync.sh` to send email notifications:

```bash
#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Activate virtual environment
source venv/bin/activate
export DJANGO_SETTINGS_MODULE=akilimo_nigeria.settings

# Run sync and capture output
OUTPUT=$(python manage.py sync_akilimo_data --batch-size=1000 2>&1)
EXIT_CODE=$?

# Log output
echo "$OUTPUT" >> logs/sync.log
echo "Sync completed at $(date) with exit code $EXIT_CODE" >> logs/sync.log

# Send email if failed
if [ $EXIT_CODE -ne 0 ]; then
    echo "$OUTPUT" | mail -s "Akilimo Sync Failed" admin@example.com
fi
```

### Run Sync in Background

Add to crontab with nohup:
```cron
0 */6 * * * nohup /Users/Apple/projects/ana_pro/run_sync.sh &
```

### Multiple Environments

For different environments (dev, staging, production):

**Development** (every 12 hours):
```cron
0 */12 * * * /path/to/dev/run_sync.sh
```

**Production** (every 6 hours):
```cron
0 */6 * * * /path/to/production/run_sync.sh
```

### Performance Optimization

For very large datasets, consider:

1. **Database Indexing** (already implemented in models)
2. **Batch Processing** (use `--batch-size` flag)
3. **Parallel Processing** (future enhancement with Celery)
4. **Incremental Sync** (sync only new/updated records)

---

## Command Reference

### Sync Command Options

```bash
python manage.py sync_akilimo_data [OPTIONS]
```

| Option | Description | Default |
|--------|-------------|---------|
| `--batch-size N` | Records per batch | 3000 |
| `--max-records N` | Maximum total records to sync | All |
| `--dry-run` | Preview without saving | False |
| `--force` | Update existing records | False |

### Examples

**Quick test (dry run):**
```bash
python manage.py sync_akilimo_data --dry-run
```

**Sync first 1000 records:**
```bash
python manage.py sync_akilimo_data --max-records=1000
```

**Full sync with update:**
```bash
python manage.py sync_akilimo_data --force --batch-size=1000
```

**Production sync (incremental):**
```bash
python manage.py sync_akilimo_data --batch-size=2000
```

---

## Logs and Reporting

### Log File Location
```
logs/sync.log
```

### Log Rotation

To prevent logs from growing too large, set up log rotation:

Create `/etc/logrotate.d/akilimo-sync`:
```
/Users/Apple/projects/ana_pro/logs/sync.log {
    daily
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 apple staff
}
```

### Sync Status Dashboard

View sync history in Django admin:
1. Navigate to: `/admin/dashboard/datasynclog/`
2. Filter by status, date range
3. Export logs for reporting

---

## Support and Maintenance

### Regular Maintenance Tasks

**Weekly:**
- Check sync logs for errors
- Verify data accuracy in dashboard
- Review sync performance metrics

**Monthly:**
- Clean up old sync logs
- Review and optimize batch sizes
- Update API credentials if needed

### Getting Help

- Check logs: `tail -f logs/sync.log`
- View sync history in Django admin
- Run manual sync with verbose output
- Contact system administrator

---

## Summary

You now have automatic data synchronization configured! Here's what's happening:

1. **Every 6 hours**, the `run_sync.sh` script runs automatically
2. It fetches the latest data from EiA MELIA API
3. Data is saved to the `AkilimoParticipant` model
4. Dashboard and homepage statistics update automatically
5. All activity is logged to `logs/sync.log`

**Next Steps:**
- Monitor the first few syncs
- Check the dashboard for updated statistics
- Review logs regularly
- Adjust sync frequency if needed

**Questions?** Check the troubleshooting section or review the sync logs.
