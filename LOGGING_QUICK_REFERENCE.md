# Logging Quick Reference

## 🚀 Quick Start

### Interactive Log Viewer (Easiest)
```bash
./view_logs.sh
```

## 📝 Common Commands

### View Errors
```bash
# Latest 50 error lines
tail -n 50 logs/akilimo_nigeria_error.log

# Watch errors in real-time
tail -f logs/akilimo_nigeria_error.log

# Count total errors
grep -c "ERROR" logs/akilimo_nigeria_error.log
```

### Search Logs
```bash
# Search for specific error
grep -i "DoesNotExist" logs/akilimo_nigeria_error.log

# Search with context (10 lines before and after)
grep -C 10 "Exception" logs/akilimo_nigeria_error.log

# Search all logs
grep -r "search_term" logs/
```

### View Specific Time Period
```bash
# View logs from specific hour
grep "2025-11-18 14:" logs/akilimo_nigeria.log

# View today's errors
grep "$(date +%Y-%m-%d)" logs/akilimo_nigeria_error.log

# View last hour
tail -n 1000 logs/akilimo_nigeria.log | grep "$(date -v-1H +%Y-%m-%d\ %H)"
```

### Analyze Patterns
```bash
# Most common errors
grep "Error Type:" logs/akilimo_nigeria_error.log | sort | uniq -c | sort -rn

# Errors by user
grep "User:" logs/akilimo_nigeria_error.log | sort | uniq -c | sort -rn

# Errors by path
grep "Path:" logs/akilimo_nigeria_error.log | sort | uniq -c | sort -rn
```

### Monitor Multiple Logs
```bash
# Monitor errors and general logs together
tail -f logs/akilimo_nigeria.log logs/akilimo_nigeria_error.log

# Monitor all logs
tail -f logs/*.log
```

## 📊 Log Files

| File | Content | Use Case |
|------|---------|----------|
| `akilimo_nigeria.log` | General application logs | Overall system activity |
| `akilimo_nigeria_error.log` | Errors with stack traces | Debugging errors |
| `akilimo_nigeria_debug.log` | Detailed debug info | Development/troubleshooting |
| `akilimo_nigeria_db.log` | Database queries | Query optimization |

## 🔧 Configuration

### Enable Debug Logging
```bash
# In .env
DEBUG=True
```

### Enable Request Logging
```bash
# In .env
LOG_ALL_REQUESTS=True
```

### Enable Database Query Logging
```bash
# In .env
DB_LOG_LEVEL=DEBUG
```

## 🐛 Debugging Workflow

1. **Reproduce the error** - Trigger the issue
2. **Check error log** - `tail -f logs/akilimo_nigeria_error.log`
3. **Find the exception** - Look for stack trace
4. **Check request details** - User, path, parameters
5. **Search for similar errors** - `grep "ErrorType" logs/*.log`
6. **Fix and test** - Apply fix and monitor logs

## 🎯 Pro Tips

### Colorize Output
```bash
# Install ccze for colorized logs
sudo apt-get install ccze  # Ubuntu/Debian
brew install ccze          # macOS

# Use it
tail -f logs/akilimo_nigeria.log | ccze -A
```

### Filter by Level
```bash
# Show only errors
grep "ERROR" logs/akilimo_nigeria.log

# Show errors and warnings
grep -E "ERROR|WARNING" logs/akilimo_nigeria.log
```

### Save Search Results
```bash
# Save errors to file
grep "ERROR" logs/akilimo_nigeria.log > errors_today.txt

# Save specific error pattern
grep "DoesNotExist" logs/akilimo_nigeria_error.log > membership_errors.txt
```

### Clean Old Logs
```bash
# Remove logs older than 30 days
find logs/ -name "*.log.*" -mtime +30 -delete

# Archive old logs
tar -czf logs_backup_$(date +%Y%m%d).tar.gz logs/*.log.*
```

## 📱 Production Server

### SSH and View Logs
```bash
ssh user@akilimonigeria.org
cd /path/to/project
./view_logs.sh
```

### Download Logs
```bash
# Download error log
scp user@server:/path/to/logs/akilimo_nigeria_error.log ./

# Download all logs
scp -r user@server:/path/to/logs/ ./logs_backup/
```

### Monitor Remotely
```bash
ssh user@server "tail -f /path/to/logs/akilimo_nigeria_error.log"
```

## 🚨 Common Issues

### No logs being created?
```bash
# Check permissions
ls -la logs/
chmod 755 logs/
touch logs/test.log  # Test write access
```

### Logs too large?
```bash
# Check sizes
du -h logs/*.log

# Rotate manually
mv logs/akilimo_nigeria.log logs/akilimo_nigeria.log.1
```

### Can't find specific error?
```bash
# Search all log files including rotated ones
grep -r "search_term" logs/
```

## 📖 What to Look For

### Critical Indicators
- `ERROR` - Something broke
- `CRITICAL` - System-level failure
- `Exception` - Unhandled errors
- `Traceback` - Python stack traces
- `500` - Server errors
- `DoesNotExist` - Missing database records
- `IntegrityError` - Database constraint violations
- `PermissionDenied` - Authorization issues

### Performance Indicators
- Multiple requests from same IP
- Slow database queries
- High frequency of specific errors
- Memory/resource warnings

## 🎓 Learn More
- [Full Logging Documentation](LOGGING_README.md)
- [Django Logging Docs](https://docs.djangoproject.com/en/stable/topics/logging/)
