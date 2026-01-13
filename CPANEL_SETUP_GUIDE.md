# cPanel Setup Guide - Automatic Data Sync
## Akilimo Nigeria Association

This guide is specifically for setting up automatic data sync on **cPanel hosting**.

---

## Quick Setup

### Step 1: Find Your Virtual Environment Path

Run this command on your cPanel server:
```bash
which python
```

This will show something like:
```
/home/akilimon/virtualenv/ana_pro/3.11/bin/python
```

The virtual environment path is everything before `/bin/python`:
```
/home/akilimon/virtualenv/ana_pro/3.11
```

### Step 2: Run Setup Script

```bash
cd ~/ana_pro
chmod +x setup_auto_sync_cpanel.sh
./setup_auto_sync_cpanel.sh
```

When prompted:
- Enter your virtual environment path (from Step 1)
- Press `y` to add cron job

### Step 3: Verify Cron Job

Check that the cron job was added:
```bash
crontab -l
```

You should see:
```
0 */6 * * * /home/akilimon/ana_pro/run_sync.sh
```

---

## Alternative: Manual Setup

If the automatic setup doesn't work, follow these manual steps:

### 1. Create Sync Script

Create `run_sync.sh` in your project directory:

```bash
cd ~/ana_pro
nano run_sync.sh
```

Paste this content (replace `YOUR_VENV_PATH` with your actual path):

```bash
#!/bin/bash
# Automated sync script for Akilimo data

# Project directory
SCRIPT_DIR="/home/akilimon/ana_pro"
cd "$SCRIPT_DIR"

# Activate virtual environment (CHANGE THIS PATH!)
source /home/akilimon/virtualenv/ana_pro/3.11/bin/activate

# Set Django settings
export DJANGO_SETTINGS_MODULE=akilimo_nigeria.settings

# Run sync
python manage.py sync_akilimo_data --batch-size=1000 >> logs/sync.log 2>&1

# Log completion
echo "Sync completed at $(date)" >> logs/sync.log
```

Save (Ctrl+O, Enter, Ctrl+X) and make executable:
```bash
chmod +x run_sync.sh
```

### 2. Create Logs Directory

```bash
mkdir -p logs
```

### 3. Test the Script

```bash
./run_sync.sh
```

Check the logs:
```bash
tail -f logs/sync.log
```

### 4. Add Cron Job via cPanel

**Method A: cPanel Interface (Easiest)**

1. Log into cPanel
2. Find and click **"Cron Jobs"**
3. Scroll to **"Add New Cron Job"**
4. Set the following:
   - **Minute**: `0`
   - **Hour**: `*/6` (every 6 hours)
   - **Day**: `*`
   - **Month**: `*`
   - **Weekday**: `*`
   - **Command**: `/home/akilimon/ana_pro/run_sync.sh`
5. Click **"Add New Cron Job"**

**Method B: Command Line**

```bash
crontab -e
```

Add this line:
```
0 */6 * * * /home/akilimon/ana_pro/run_sync.sh
```

Save and exit.

---

## Testing

### Test Sync Command Directly

```bash
cd ~/ana_pro
source /home/akilimon/virtualenv/ana_pro/3.11/bin/activate
python manage.py sync_akilimo_data --dry-run
```

### Test Full Sync

```bash
cd ~/ana_pro
./run_sync.sh
```

### Check Logs

```bash
tail -20 logs/sync.log
```

### Verify Data in Database

```bash
cd ~/ana_pro
source /home/akilimon/virtualenv/ana_pro/3.11/bin/activate
python manage.py shell
```

Then:
```python
from dashboard.models import AkilimoParticipant, DataSyncLog

# Check participant count
print(f"Total participants: {AkilimoParticipant.objects.count()}")

# Check latest sync
latest = DataSyncLog.objects.latest('started_at')
print(f"Latest sync: {latest.status} - {latest.records_created} created")
```

---

## Common cPanel Issues & Solutions

### Issue 1: Virtual Environment Not Found

**Error**: `Virtual environment not found`

**Solution**: Find your venv path:
```bash
which python
echo $VIRTUAL_ENV
find ~ -name "activate" -path "*/bin/activate" 2>/dev/null
```

Update `run_sync.sh` with the correct path.

### Issue 2: Permission Denied

**Error**: `Permission denied`

**Solution**:
```bash
chmod +x run_sync.sh
chmod +x setup_auto_sync_cpanel.sh
```

### Issue 3: Python Command Not Found

**Error**: `python: command not found`

**Solution**: Use `python3` instead of `python` in `run_sync.sh`:
```bash
python3 manage.py sync_akilimo_data --batch-size=1000 >> logs/sync.log 2>&1
```

### Issue 4: Django Settings Not Found

**Error**: `No module named 'akilimo_nigeria'`

**Solution**: Ensure you're in the project directory:
```bash
cd /home/akilimon/ana_pro
pwd  # Should show /home/akilimon/ana_pro
```

Update `run_sync.sh` to include `cd` command.

### Issue 5: Cron Job Not Running

**Possible causes**:
1. Wrong path in cron command
2. Script not executable
3. Virtual environment path incorrect

**Debug**:
```bash
# Check cron jobs
crontab -l

# Check cron logs (cPanel)
tail -50 ~/logs/cron.log

# Test script manually
bash -x ./run_sync.sh
```

---

## cPanel-Specific Notes

### Email Notifications

cPanel automatically sends email for cron output. To disable:
```
0 */6 * * * /home/akilimon/ana_pro/run_sync.sh >/dev/null 2>&1
```

To enable only error emails:
```
0 */6 * * * /home/akilimon/ana_pro/run_sync.sh >/dev/null
```

### Resource Limits

cPanel has resource limits. If sync fails:
1. Reduce batch size: `--batch-size=500`
2. Limit records: `--max-records=5000`
3. Contact hosting support to increase limits

### Python Version

Check your Python version:
```bash
python --version
python3 --version
```

Ensure it matches your virtual environment (3.11 recommended).

---

## Monitoring on cPanel

### View Logs

```bash
# Sync logs
tail -f ~/ana_pro/logs/sync.log

# Cron logs
tail -f ~/logs/cron.log
```

### Check Disk Space

Logs can grow large:
```bash
du -sh ~/ana_pro/logs/
```

Rotate logs if needed:
```bash
mv logs/sync.log logs/sync.log.old
touch logs/sync.log
```

### Check Cron History

Via cPanel:
1. Log into cPanel
2. Go to **Cron Jobs**
3. Scroll down to see **"Current Cron Jobs"**

---

## Support

### Get Help

1. **Check logs**:
   ```bash
   tail -50 logs/sync.log
   ```

2. **Test manually**:
   ```bash
   source /home/akilimon/virtualenv/ana_pro/3.11/bin/activate
   python manage.py sync_akilimo_data --dry-run
   ```

3. **Verify cron**:
   ```bash
   crontab -l
   ```

### Contact Support

If issues persist:
- Check Django admin: Dashboard → Data Sync Logs
- Contact hosting support for resource limits
- Review error messages in logs

---

## Summary

**Your setup checklist:**
- ✅ Virtual environment path identified
- ✅ `run_sync.sh` created and executable
- ✅ Logs directory created
- ✅ Cron job added (every 6 hours)
- ✅ Test sync completed successfully
- ✅ Monitoring logs

**Sync schedule:** Every 6 hours (12 AM, 6 AM, 12 PM, 6 PM)

**Next sync:** Check with `crontab -l` and calculate based on current time.

---

**Need the full path to your virtual environment?**

Run this finder script:
```bash
cat > ~/find_venv.sh << 'EOF'
#!/bin/bash
echo "Looking for virtual environments..."
echo ""
echo "Method 1: Current environment"
echo "VIRTUAL_ENV: $VIRTUAL_ENV"
echo ""
echo "Method 2: Python location"
which python
which python3
echo ""
echo "Method 3: Common cPanel locations"
find ~ -maxdepth 4 -name "activate" -path "*/bin/activate" 2>/dev/null
EOF

chmod +x ~/find_venv.sh
./find_venv.sh
```

This will show all possible virtual environment locations!
