# Incident Response Runbooks - Deal Scout

**Quick Navigation:**
- [High Error Rate](#high-error-rate)
- [Database Unreachable](#database-unreachable)
- [Redis Unreachable](#redis-unreachable)
- [Task Queue Stuck](#task-queue-stuck)
- [Memory Issues](#memory-issues)
- [Disk Full](#disk-full)
- [API Latency](#api-latency)
- [Marketplace Integration Failures](#marketplace-integration-failures)
- [Notification Delivery Failures](#notification-delivery-failures)
- [Rollback Procedure](#rollback-procedure)

---

## High Error Rate

**Alert**: Error rate > 5% for 5 minutes
**Severity**: CRITICAL
**Expected Duration**: 15-30 minutes

### Immediate Actions (0-5 minutes)

1. **Check Dashboard**
   ```
   - Open Grafana dashboard
   - Look at error rate trend (last 1 hour)
   - Check which endpoints are failing
   ```

2. **Verify Service Health**
   ```bash
   curl -s http://localhost:8000/health | jq .
   # Check: db, redis, queue_depth
   ```

3. **Check Recent Logs**
   ```bash
   docker-compose logs --tail 100 backend | grep ERROR
   # or
   tail -100 /var/log/deal-scout/app.log | grep ERROR
   ```

### Investigation (5-15 minutes)

1. **Identify Error Pattern**
   - Is it affecting all endpoints or specific ones?
   - Is it new errors or existing issue escalating?
   - Check if errors correlate with specific time or event

2. **Check External Dependencies**
   ```bash
   # Test database
   psql $DATABASE_URL -c "SELECT 1"

   # Test Redis
   redis-cli ping

   # Test API integrations
   curl -s https://api.ebay.com/api/health
   ```

3. **Review Code Changes**
   ```bash
   git log --oneline -10
   git diff HEAD~1..HEAD
   ```

### Resolution

**If Database is Down:**
- See [Database Unreachable](#database-unreachable) runbook

**If Redis is Down:**
- See [Redis Unreachable](#redis-unreachable) runbook

**If Specific Endpoint Failing:**
   ```bash
   # Check application logs for detailed error
   docker-compose logs backend | grep "<endpoint>"

   # Check if recent deployment caused issue
   docker-compose ps  # Check image version
   ```

**If Transient Issue:**
   ```bash
   # Restart backend
   docker-compose restart backend

   # Monitor error rate
   watch -n 5 'curl -s http://localhost:8000/metrics | grep "request.*5"'
   ```

### Escalation

If error rate remains > 5% after 15 minutes:
1. Page on-call engineer
2. Consider rollback (see [Rollback Procedure](#rollback-procedure))
3. Failover to previous deployment

---

## Database Unreachable

**Alert**: PostgreSQL connection failed
**Severity**: CRITICAL
**Expected Duration**: 20-40 minutes

### Immediate Actions (0-2 minutes)

1. **Verify Database Status**
   ```bash
   # Check if container is running
   docker-compose ps postgres

   # Check logs
   docker-compose logs postgres

   # Try connection
   psql $DATABASE_URL -c "SELECT 1"
   ```

2. **Check Connection Details**
   ```bash
   # Verify DATABASE_URL is correct
   echo $DATABASE_URL

   # Check network connectivity
   docker-compose exec backend curl -v postgres:5432
   ```

3. **Stop Application Traffic**
   ```bash
   # If managed load balancer, drain connections
   # Prevent new requests from being accepted
   ```

### Investigation (2-10 minutes)

1. **Database Disk Space**
   ```bash
   # Inside postgres container
   docker-compose exec postgres du -sh /var/lib/postgresql/data

   # Check container logs
   docker-compose logs postgres | tail -50
   ```

2. **Database Locks**
   ```sql
   -- If you can connect
   SELECT * FROM pg_locks;
   SELECT * FROM pg_stat_activity WHERE state != 'idle';
   ```

3. **Memory/CPU Issues**
   ```bash
   docker stats postgres
   ```

### Resolution

**If Database is Out of Disk Space:**
1. Free up disk space (delete old logs, backups)
2. Restart PostgreSQL
3. Monitor recovery

**If Database is Locked/Hung:**
   ```bash
   # Restart database container
   docker-compose restart postgres

   # Wait for startup
   sleep 30

   # Verify
   docker-compose exec postgres pg_isready
   ```

**If Connection Pool Exhausted:**
   ```bash
   # Restart application to reset connection pool
   docker-compose restart backend
   ```

**If Replication Lag (RDS):**
   ```bash
   # Failover to replica
   # Via AWS console or CLI:
   aws rds failover-db-cluster --db-cluster-identifier deal-scout
   ```

### Recovery Checklist

- [ ] Database accepting connections
- [ ] Tables accessible and not corrupted
- [ ] Replication caught up (if applicable)
- [ ] Application reconnected successfully
- [ ] Traffic resumed
- [ ] Error rate returned to normal

---

## Redis Unreachable

**Alert**: Redis connection failed
**Severity**: HIGH
**Expected Duration**: 10-20 minutes

### Immediate Actions (0-2 minutes)

1. **Verify Redis Status**
   ```bash
   # Check container
   docker-compose ps redis

   # Try connection
   redis-cli ping

   # Check logs
   docker-compose logs redis
   ```

2. **Check Memory**
   ```bash
   redis-cli info memory
   ```

### Investigation (2-5 minutes)

1. **If Out of Memory**
   ```bash
   # Check queue depth
   redis-cli LLEN celery

   # Check memory fragmentation
   redis-cli info memory | grep fragmentation
   ```

2. **If Corrupted**
   ```bash
   # Check RDB file
   ls -lh /var/lib/redis/dump.rdb
   ```

### Resolution

**Normal Restart:**
   ```bash
   docker-compose restart redis

   # Verify
   redis-cli ping
   ```

**If Out of Memory:**
   1. Kill non-critical processes
   2. Reduce max memory
   3. Clear old data
   ```bash
   redis-cli FLUSHALL  # WARNING: Clears all data
   ```

**If Corrupted:**
   ```bash
   # Backup corrupted file
   cp /var/lib/redis/dump.rdb /var/lib/redis/dump.rdb.backup

   # Remove corrupted file
   rm /var/lib/redis/dump.rdb

   # Restart
   docker-compose restart redis
   ```

### Important Notes

- Restarting Redis will lose all cached data
- Task queue will be cleared (rescan will happen)
- Cache warmup will happen gradually
- Monitor for spike in database load

---

## Task Queue Stuck

**Alert**: Queue depth > 1000 for 10 minutes
**Severity**: HIGH
**Expected Duration**: 15-30 minutes

### Immediate Actions (0-5 minutes)

1. **Check Queue Status**
   ```bash
   # Queue depth
   redis-cli LLEN celery

   # Active tasks
   celery -A app.worker inspect active

   # Worker stats
   celery -A app.worker inspect stats
   ```

2. **Check Worker Health**
   ```bash
   # See if workers are running
   docker-compose ps worker

   # Check logs
   docker-compose logs worker | tail -50
   ```

3. **Verify Beat Scheduler**
   ```bash
   docker-compose ps beat
   docker-compose logs beat | tail -50
   ```

### Investigation (5-15 minutes)

1. **Identify Stuck Tasks**
   ```bash
   # Get active task details
   celery -A app.worker inspect active_queues

   # Get task details
   celery -A app.worker inspect query_task scan_all
   ```

2. **Check Resource Usage**
   ```bash
   docker stats worker
   # Is it CPU bound, memory bound, or waiting?
   ```

3. **Check for Errors**
   ```bash
   # Failed tasks
   celery -A app.worker inspect failed

   # Reserved tasks
   celery -A app.worker inspect reserved
   ```

### Resolution

**If Workers are Dead:**
   ```bash
   docker-compose restart worker

   # Monitor queue clearing
   watch -n 5 'redis-cli LLEN celery'
   ```

**If Workers are Hung:**
   ```bash
   # Kill hung processes
   docker-compose kill worker
   docker-compose rm worker
   docker-compose up -d worker
   ```

**If Specific Task Stuck:**
   ```bash
   # Purge failed tasks
   celery -A app.worker purge

   # WARNING: This will clear all tasks!
   # Use only if workers are completely stuck
   ```

**If Beat Scheduler Stuck:**
   ```bash
   docker-compose restart beat

   # Verify schedule restored
   celery -A app.worker inspect scheduled
   ```

### Recovery Checklist

- [ ] Workers running and healthy
- [ ] Queue depth decreasing
- [ ] New tasks being processed
- [ ] Beat scheduler executing schedules
- [ ] Error rate normal

---

## Memory Issues

**Alert**: Memory usage > 85% for 10 minutes
**Severity**: WARNING
**Expected Duration**: 10-20 minutes

### Immediate Actions (0-5 minutes)

1. **Check Memory Usage**
   ```bash
   docker stats
   # Identify which service is using memory

   # Check inside container
   docker-compose exec backend free -h
   ```

2. **Check for Memory Leaks**
   ```bash
   # Monitor growth over time
   watch -n 5 'docker stats --no-stream'
   ```

### Investigation (5-10 minutes)

**For Backend:**
   ```bash
   # Check for large query results
   docker-compose logs backend | grep "loaded X objects"

   # Check for open connections
   psql $DATABASE_URL -c "SELECT count(*) FROM pg_stat_activity"
   ```

**For Worker:**
   ```bash
   # Check for stuck tasks
   celery -A app.worker inspect active | wc -l
   ```

**For Database:**
   ```bash
   # Check buffer usage
   psql $DATABASE_URL -c "SELECT * FROM pg_stat_database WHERE datname = 'deals'"
   ```

### Resolution

**Temporary (Quick Relief):**
1. Restart the high-memory service
2. This may cause brief downtime but releases memory

**Permanent (Root Cause):**
1. Identify memory leak source
2. Deploy fix in next release
3. Monitor for recurrence

**Restart Service:**
   ```bash
   docker-compose restart backend  # or worker, postgres, redis

   # Monitor
   docker stats --no-stream
   ```

---

## Disk Full

**Alert**: Disk space < 5%
**Severity**: CRITICAL
**Expected Duration**: 30-60 minutes

### Immediate Actions (0-2 minutes)

1. **Check Disk Usage**
   ```bash
   df -h
   du -sh /*
   ```

2. **Identify Large Files**
   ```bash
   # Find files > 100MB
   find / -type f -size +100M -exec ls -lh {} \; 2>/dev/null
   ```

### Investigation (2-10 minutes)

1. **Check Log Files**
   ```bash
   du -sh /var/log/*
   ls -lhS /var/log/deal-scout/
   ```

2. **Check Database**
   ```bash
   du -sh /var/lib/postgresql/data
   du -sh /var/backups/postgresql
   ```

3. **Check Container Logs**
   ```bash
   # Docker stores logs
   du -sh /var/lib/docker/containers/
   ```

### Resolution

**Clean Log Files:**
   ```bash
   # Safely delete old logs
   find /var/log/deal-scout -name "*.log.*" -mtime +7 -delete

   # Or rotate
   logrotate -f /etc/logrotate.conf
   ```

**Clean Database Backups:**
   ```bash
   # Delete old backups older than 7 days
   find /var/backups/postgresql -mtime +7 -delete
   ```

**Clean Docker Logs:**
   ```bash
   # Prune unused images/containers/volumes
   docker system prune -a

   # Clear log files (be careful!)
   find /var/lib/docker/containers -name "*.log" -delete
   ```

**Temporary: Clean tmp Files:**
   ```bash
   # Remove temp files
   rm -rf /tmp/*
   rm -rf /var/tmp/*
   ```

### Prevention

Set up log rotation in `/etc/logrotate.d/deal-scout`:
```
/var/log/deal-scout/*.log {
    daily
    rotate 7
    compress
    delaycompress
    notifempty
    create 0644 root root
    postrotate
        docker-compose kill -s HUP backend
    endscript
}
```

---

## API Latency

**Alert**: p95 latency > 500ms
**Severity**: WARNING
**Expected Duration**: 10-30 minutes

### Investigation

1. **Check Database Queries**
   ```bash
   # Find slow queries
   psql $DATABASE_URL -c "
   SELECT mean_exec_time, calls, query
   FROM pg_stat_statements
   ORDER BY mean_exec_time DESC
   LIMIT 10"
   ```

2. **Check Load**
   ```bash
   # Current request rate
   curl -s http://localhost:8000/metrics | grep "requests_total"

   # Connection count
   psql $DATABASE_URL -c "SELECT count(*) FROM pg_stat_activity"
   ```

3. **Check Resources**
   ```bash
   docker stats backend
   ```

### Resolution

**Scale Horizontally:**
   ```bash
   # Increase backend replicas
   docker-compose up -d --scale backend=5
   ```

**Optimize Queries:**
   ```bash
   # Add indexes (see optimize_database.sql)
   psql $DATABASE_URL < scripts/optimize_database.sql
   ```

**Clear Cache:**
   ```bash
   redis-cli FLUSHALL
   # This will flush all cache, triggering refresh
   ```

**Restart Backend:**
   ```bash
   docker-compose restart backend
   ```

---

## Marketplace Integration Failures

**Alert**: eBay API errors > 10 in 5 minutes
**Severity**: WARNING
**Expected Duration**: 15-45 minutes

### Investigation

1. **Check API Status**
   - Visit: https://status.ebay.com
   - Check Twitter: @eBayAPIPlatform

2. **Check Credentials**
   ```bash
   # Verify credentials are still valid
   echo $EBAY_APP_ID
   echo $EBAY_ENV
   ```

3. **Check Recent Errors**
   ```bash
   docker-compose logs backend | grep -i ebay | tail -20
   ```

### Resolution

**If eBay API is Down:**
- Wait for restoration
- Monitor /health endpoint
- Resume scanning once API is up

**If Credentials Invalid:**
1. Refresh OAuth token
2. Update credentials
3. Restart scanner

**If Rate Limited:**
1. Reduce scan frequency
2. Implement exponential backoff
3. Check quota usage

---

## Notification Delivery Failures

**Alert**: Email failure rate > 10%
**Severity**: WARNING
**Expected Duration**: 15-30 minutes

### Investigation

1. **Check SMTP Connectivity**
   ```bash
   telnet $SMTP_HOST $SMTP_PORT
   ```

2. **Check Credentials**
   ```bash
   echo $SMTP_USER
   echo $SMTP_PASSWORD  # Don't share!
   ```

3. **Check Recent Errors**
   ```bash
   docker-compose logs backend | grep -i "smtp\|email" | tail -20
   ```

4. **Check Email Queue**
   ```bash
   # Unsent notifications
   psql $DATABASE_URL -c "SELECT count(*) FROM notifications WHERE status = 'pending'"
   ```

### Resolution

**If SMTP Server Down:**
- Contact email provider
- Monitor status page
- Retry notifications once restored

**If Credentials Invalid:**
1. Update SMTP credentials
2. Test connection
3. Restart application

**If Rate Limited:**
1. Reduce sending frequency
2. Batch notifications
3. Check provider limits

**Retry Failed Notifications:**
   ```bash
   # Manually trigger retry
   docker-compose exec backend celery -A app.worker.celery_app -c 1 call app.tasks.notify.send_notifications
   ```

---

## Rollback Procedure

**Use when**: Critical issue requires immediate reversal
**Duration**: 10-15 minutes total

### Pre-Rollback

1. **Verify Issue is from Recent Deployment**
   ```bash
   git log --oneline -5
   ```

2. **Identify Previous Good Version**
   ```bash
   git log --oneline | grep -i "stable\|release"
   ```

### Rollback Steps

1. **Stop Current Deployment**
   ```bash
   docker-compose down
   ```

2. **Checkout Previous Version**
   ```bash
   git log --oneline -10
   git checkout <previous-commit>  # Use commit hash before problematic change
   ```

3. **Rebuild Images**
   ```bash
   docker-compose build --no-cache
   ```

4. **Start Services**
   ```bash
   docker-compose up -d
   ```

5. **Verify Rollback**
   ```bash
   # Check health
   curl http://localhost:8000/health

   # Check logs
   docker-compose logs backend | tail -20

   # Verify error rate
   sleep 30
   curl http://localhost:8000/metrics | grep "requests_total"
   ```

### Post-Rollback

1. **Notify Team**
   - Slack/Email: "Rollback completed. System stable."
   - Document: What was rolled back and why

2. **Root Cause Analysis**
   - When the incident is stable
   - Review what went wrong
   - Implement preventive measures

3. **Revert to Good Version**
   ```bash
   # Pull latest stable
   git checkout main
   git pull origin main
   ```

---

## Escalation Policy

### Response Times

| Severity | Initial Response | Resolution Target |
|----------|------------------|-------------------|
| CRITICAL | < 2 minutes | < 30 minutes |
| HIGH | < 5 minutes | < 1 hour |
| WARNING | < 15 minutes | < 4 hours |

### Escalation Path

1. **On-Call Engineer**
   - First responder
   - Runs runbooks
   - Gathers initial data

2. **Senior Engineer**
   - If not resolved in 15 minutes (CRITICAL) / 30 minutes (HIGH)
   - Code review authority
   - Database expert

3. **Engineering Lead**
   - If not resolved in 30 minutes (CRITICAL)
   - Deployment authority
   - Architecture decisions

4. **Executive/Customer**
   - If SLA breached or multi-hour outage
   - CEO/VP notification
   - Customer communication

### Contact Information

```
On-Call: See PagerDuty rotation
Slack: #deal-scout-incidents
Email: team@example.com
```

---

## Post-Incident Review

After any SEV1/SEV2 incident:

1. **Timeline**
   - When was it detected?
   - When was it resolved?
   - Total duration?

2. **Root Cause**
   - What caused it?
   - Why wasn't it caught earlier?

3. **Impact**
   - How many users affected?
   - Data loss?
   - Revenue impact?

4. **Prevention**
   - What monitoring/alerts needed?
   - What code changes needed?
   - What process improvements?

5. **Action Items**
   - Assign owners
   - Set target dates
   - Track completion

---

**Last Updated**: January 15, 2024
**Review Cadence**: Monthly
**Version**: 1.0
