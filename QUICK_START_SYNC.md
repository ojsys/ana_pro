# Quick Start: Automatic Data Sync

## Setup (One-Time)

Run the setup script:
```bash
./setup_auto_sync.sh
```

When prompted, press `y` to add the cron job.

## Done! 

Your data will now sync automatically every 6 hours.

---

## Quick Commands

### Test Sync Manually
```bash
source venv/bin/activate
python manage.py sync_akilimo_data --dry-run
```

### Run Sync Now
```bash
./run_sync.sh
```

### View Logs
```bash
tail -f logs/sync.log
```

### Check Cron Job
```bash
crontab -l
```

### View Sync History
Django Admin → Dashboard → Data Sync Logs

---

## What's Syncing?

- ✅ Farmer/participant records
- ✅ Geographic data (states, cities)  
- ✅ Partner organizations
- ✅ Training events
- ✅ Demographics & gender data

## Schedule

**Every 6 hours** at: 12:00 AM, 6:00 AM, 12:00 PM, 6:00 PM

---

For detailed documentation, see [AUTO_SYNC_GUIDE.md](AUTO_SYNC_GUIDE.md)
