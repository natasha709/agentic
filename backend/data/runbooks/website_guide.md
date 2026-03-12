# Website Performance Troubleshooting

## Rapid Assessment Checklist

### 1. **Server Metrics (First 60 seconds)**
```
# CPU/Memory/Disk
top -n1 | head -20
free -h
df -h

# Web server status
systemctl status nginx/apache2
ss -tulpn | grep :80
```

### 2. **Application Logs (Next 2 minutes)**
```
# Nginx/Apache access logs
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log

# Application logs
tail -f /var/log/app/app.log
journalctl -u app -f
```

### 3. **Database Health**
```
# Connection count
mysql -e "SHOW PROCESSLIST;"
psql -c "SELECT * FROM pg_stat_activity;"

# Slow queries
mysql -e "SHOW FULL PROCESSLIST;" | grep Sleep
```

## Common Issues Matrix

| Symptom | Likely Cause | First Action |
|---------|--------------|--------------|
| 502/504 | Backend down | `systemctl status app` |
| 503 | Resource exhaustion | Check CPU/RAM |
| Slow load | Database bottleneck | Kill slow queries |
| Static assets fail | CDN issue | Test direct server |

## Performance Optimization

### Immediate Fixes
```
# Restart web server (graceful)
systemctl reload nginx

# Clear cache
rm -rf /var/cache/nginx/*
redis-cli FLUSHALL  # if using Redis

# Restart app
systemctl restart app
```

### Monitoring Commands
```
# Real-time metrics
watch -n1 'echo "CPU: $(top -bn1 | grep "Cpu(s)" | awk "{print \$2}")"'

# Apache/Nginx status
curl -s http://localhost/server-status | grep requests

# Database connections
netstat -an | grep :3306 | wc -l
```

## Escalation Path
1. **5 min**: Restart services + clear cache
2. **15 min**: Database optimization
3. **30 min**: Scale horizontally
4. **1 hr**: Engage SRE team
