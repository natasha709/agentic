# Disk Space Management Guide

## Emergency Space Recovery (First 5 minutes)

### Find Big Files/Directories
```bash
# Top 10 largest directories
du -sh * | sort -hr | head -10

# Largest files in current dir
find . -type f -size +100M -exec ls -lh {} \; | sort -hr

# Global largest files
sudo du -ah / | sort -rh | head -20
```

### Quick Wins
```
# Clean package cache
sudo apt clean
sudo yum clean packages

# Remove old logs
sudo find /var/log -type f -name "*.log" -mtime +30 -delete

# Docker cleanup
docker system prune -af
docker volume prune -f
```

## Find Space Hogs by Type

```
# Log files eating space
sudo du -sh /var/log/* | sort -hr

# User home directories
sudo du -sh /home/* | sort -hr

# Temp files
sudo du -sh /tmp/* | sort -hr

# Core dumps
sudo find / -name "core*" -size +10M 2>/dev/null
```

## Prevention & Monitoring

### Automated Cleanup Script
```bash
#!/bin/bash
# Daily cleanup
find /var/log -name "*.log.*" -mtime +7 -delete
find /tmp -mtime +1 -delete
docker image prune -f
```

### Alerts
```
# Alert at 85% usage
df -h | awk '$5+0 > 85 {print $0}' | mail -s "Disk Alert" admin@company.com
```

## Long-term Solutions
1. **Add storage** (fastest)
2. **Data lifecycle policy**
3. **Compression/archiving**
4. **Move to object storage**

**Escalation**: If root cause unknown after 30 min → Storage team
