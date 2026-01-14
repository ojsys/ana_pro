# Quick Steps: Update API Token

## When You Get the New Token

### Option 1: Via Django Admin (Easiest)

1. Go to: `https://your-domain.com/admin/`
2. Navigate to: **Dashboard → API Configurations**
3. Click on **"EiA MELIA API"**
4. Replace the **Token** field with the new token
5. Ensure **Is Active** is checked ✓
6. Click **Save**

---

### Option 2: Via Command Line

```bash
cd ~/ana_pro
source ~/virtualenv/ana_pro/3.11/bin/activate
python manage.py shell
```

Then:

```python
from dashboard.models import APIConfiguration

# Get the configuration
config = APIConfiguration.objects.filter(is_active=True).first()

# Update the token
config.token = 'PASTE_YOUR_NEW_TOKEN_HERE'
config.save()

print("✅ Token updated successfully!")
exit()
```

---

## After Updating the Token

### Step 1: Test the API Connection

```bash
cd ~/ana_pro
source ~/virtualenv/ana_pro/3.11/bin/activate
python manage.py shell
```

```python
from dashboard.models import APIConfiguration
from dashboard.services import EiAMeliaAPIService

config = APIConfiguration.objects.filter(is_active=True).first()
api = EiAMeliaAPIService(config.token)

try:
    result = api.get_participants_by_usecase('akilimo', page=1, page_size=1)
    print(f"✅ SUCCESS! Total records: {result.get('count', 0)}")
except Exception as e:
    print(f"❌ Still not working: {e}")

exit()
```

### Step 2: Test Dry Run

```bash
python manage.py sync_akilimo_data --dry-run
```

You should see:
```
✅ Using API: EiA MELIA API
📊 Total records available: [some number]
```

### Step 3: Run Small Test Sync

```bash
python manage.py sync_akilimo_data --max-records=100
```

### Step 4: Run Full Sync

```bash
python manage.py sync_akilimo_data
```

### Step 5: Setup Cron Job

Once sync works, add the cron job:

**Via cPanel Interface:**
- Minute: `0`
- Hour: `*/6`
- Day: `*`
- Month: `*`
- Weekday: `*`
- Command: `/home/akilimon/ana_pro/run_sync_cpanel.sh`

**Or via command line:**
```bash
crontab -e
```
Add:
```
0 */6 * * * /home/akilimon/ana_pro/run_sync_cpanel.sh
```

---

## Current Status

✅ Homepage shows real-time statistics from database
✅ JavaScript auto-refreshes stats every 5 minutes
✅ Sync script created: `run_sync_cpanel.sh`
✅ Virtual environment path configured: `~/virtualenv/ana_pro/3.11`
⏳ Waiting for valid API token from EiA MELIA
⏳ Pending: Setup automatic 6-hour sync via cron

---

## Quick Reference Commands

**Activate environment:**
```bash
source ~/virtualenv/ana_pro/3.11/bin/activate
```

**Test sync:**
```bash
python manage.py sync_akilimo_data --dry-run
```

**View logs:**
```bash
tail -f logs/sync.log
```

**Check cron jobs:**
```bash
crontab -l
```

---

**When you return with the new token, start with Option 1 or Option 2 above to update it, then proceed with the testing steps!**
