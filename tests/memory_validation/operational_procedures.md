# Memory System Operational Procedures

## Table of Contents
1. [System Monitoring](#system-monitoring)
2. [Troubleshooting Guide](#troubleshooting-guide)
3. [Backup and Recovery](#backup-and-recovery)
4. [Performance Tuning](#performance-tuning)
5. [Maintenance Procedures](#maintenance-procedures)
6. [Emergency Response](#emergency-response)

## System Monitoring

### Daily Health Checks

1. **Database Health**
   ```bash
   # Check database connectivity
   psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c "SELECT 1"
   
   # Check table sizes
   psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c "
   SELECT schemaname, tablename, 
          pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
   FROM pg_tables 
   WHERE schemaname = 'public' 
   ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;"
   
   # Check active connections
   psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c "
   SELECT count(*) as connection_count 
   FROM pg_stat_activity 
   WHERE state = 'active';"
   ```

2. **API Health**
   ```bash
   # Check internal API
   curl -X GET http://localhost:8001/health
   
   # Check external API
   curl -X GET http://localhost:8443/health
   
   # Check MCP API
   curl -X GET http://localhost:8002/health
   ```

3. **ChromaDB Health**
   ```bash
   # Check ChromaDB status
   curl -X GET http://localhost:8000/api/v1/heartbeat
   ```

### Performance Monitoring

1. **Response Time Monitoring**
   ```python
   # Monitor API response times
   python tests/memory_validation/run_performance_benchmarks.py --quick-check
   ```

2. **Resource Usage Monitoring**
   ```bash
   # Check memory usage
   ps aux | grep -E "memory-service|chroma" | awk '{sum+=$6} END {print "Total Memory (MB):", sum/1024}'
   
   # Check CPU usage
   top -b -n 1 | grep -E "memory-service|chroma"
   ```

3. **Database Performance**
   ```sql
   -- Long running queries
   SELECT pid, now() - pg_stat_activity.query_start AS duration, query 
   FROM pg_stat_activity 
   WHERE (now() - pg_stat_activity.query_start) > interval '5 minutes';
   
   -- Index usage
   SELECT schemaname, tablename, indexname, idx_scan
   FROM pg_stat_user_indexes
   ORDER BY idx_scan;
   ```

### Alert Thresholds

| Metric | Warning | Critical | Action |
|--------|---------|----------|--------|
| API Response Time | >500ms | >2000ms | Check database queries |
| Database Connections | >80% pool | >95% pool | Scale connection pool |
| Memory Usage | >70% | >90% | Restart services |
| Error Rate | >1% | >5% | Check logs immediately |
| ChromaDB Collection Size | >1M vectors | >5M vectors | Consider sharding |

## Troubleshooting Guide

### Common Issues and Solutions

#### 1. Database Connection Failures

**Symptoms:**
- API returns 500 errors
- "connection refused" in logs
- Timeout errors

**Diagnosis:**
```bash
# Check if database is running
pg_isready -h $DB_HOST -p $DB_PORT

# Check connection pool status
psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c "
SELECT count(*) as total_connections,
       count(*) FILTER (WHERE state = 'active') as active,
       count(*) FILTER (WHERE state = 'idle') as idle
FROM pg_stat_activity;"
```

**Solutions:**
1. Restart database connection pool
2. Increase pool size in configuration
3. Check network connectivity
4. Verify database credentials

#### 2. Slow Query Performance

**Symptoms:**
- High API response times
- Database CPU usage spike
- Timeout errors

**Diagnosis:**
```sql
-- Find slow queries
SELECT query, mean_exec_time, calls
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 10;

-- Check missing indexes
SELECT schemaname, tablename, attname, n_distinct, correlation
FROM pg_stats
WHERE schemaname = 'public'
AND n_distinct > 100
AND correlation < 0.1
ORDER BY n_distinct DESC;
```

**Solutions:**
1. Add missing indexes
2. Optimize query patterns
3. Implement query caching
4. Consider database partitioning

#### 3. Memory Service Crashes

**Symptoms:**
- Service restarts frequently
- Out of memory errors
- Unresponsive API

**Diagnosis:**
```bash
# Check service logs
journalctl -u memory-service -n 100

# Check memory limits
cat /proc/$(pgrep -f memory-service)/limits | grep "Max memory"

# Monitor memory growth
while true; do
  ps aux | grep memory-service | awk '{print $6/1024 " MB"}'
  sleep 5
done
```

**Solutions:**
1. Increase memory limits
2. Implement request rate limiting
3. Fix memory leaks
4. Enable garbage collection tuning

#### 4. ChromaDB Issues

**Symptoms:**
- Vector search failures
- Embedding errors
- Collection not found

**Diagnosis:**
```python
# Check ChromaDB collections
import chromadb
client = chromadb.HttpClient(host="localhost", port=8000)
print(client.list_collections())

# Verify collection health
for collection in client.list_collections():
    print(f"{collection.name}: {collection.count()} vectors")
```

**Solutions:**
1. Restart ChromaDB service
2. Rebuild vector indexes
3. Check disk space
4. Verify embedding dimensions

### Error Code Reference

| Error Code | Description | Solution |
|------------|-------------|----------|
| MEM-001 | Database connection timeout | Check database status and network |
| MEM-002 | Invalid entity data | Validate input against schema |
| MEM-003 | Client not found | Verify client_id exists |
| MEM-004 | Duplicate entity | Use update instead of create |
| MEM-005 | Vector dimension mismatch | Check embedding model consistency |
| MEM-006 | Rate limit exceeded | Implement backoff strategy |
| MEM-007 | Authentication failed | Verify JWT token and scope |
| MEM-008 | Schema validation failed | Check object_schemas table |

## Backup and Recovery

### Automated Backup Procedures

1. **Database Backup Script**
   ```bash
   #!/bin/bash
   # backup_memory_system.sh
   
   BACKUP_DIR="/backups/memory-system"
   TIMESTAMP=$(date +%Y%m%d_%H%M%S)
   
   # Backup PostgreSQL
   pg_dump -h $DB_HOST -U $DB_USER -d $DB_NAME \
     --format=custom \
     --file="$BACKUP_DIR/postgres_$TIMESTAMP.dump"
   
   # Backup ChromaDB
   docker exec chroma-container \
     tar -czf - /chroma/data > "$BACKUP_DIR/chroma_$TIMESTAMP.tar.gz"
   
   # Verify backups
   pg_restore --list "$BACKUP_DIR/postgres_$TIMESTAMP.dump" > /dev/null
   if [ $? -eq 0 ]; then
     echo "PostgreSQL backup verified"
   else
     echo "PostgreSQL backup failed!"
     exit 1
   fi
   ```

2. **Backup Schedule**
   ```cron
   # Crontab entries
   0 2 * * * /opt/scripts/backup_memory_system.sh  # Daily at 2 AM
   0 */6 * * * /opt/scripts/backup_memory_system.sh --incremental  # Every 6 hours
   ```

### Recovery Procedures

1. **Database Recovery**
   ```bash
   # Stop services
   systemctl stop memory-service
   
   # Restore database
   pg_restore -h $DB_HOST -U $DB_USER -d $DB_NAME \
     --clean --if-exists \
     /backups/memory-system/postgres_20240115_020000.dump
   
   # Verify restoration
   psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c "
   SELECT COUNT(*) FROM memory_entities;"
   ```

2. **ChromaDB Recovery**
   ```bash
   # Stop ChromaDB
   docker stop chroma-container
   
   # Restore data
   docker run --rm -v chroma-data:/chroma/data \
     -v /backups:/backups \
     alpine tar -xzf /backups/chroma_20240115_020000.tar.gz -C /
   
   # Restart ChromaDB
   docker start chroma-container
   ```

### Disaster Recovery Plan

1. **RTO (Recovery Time Objective)**: 4 hours
2. **RPO (Recovery Point Objective)**: 6 hours

**Recovery Steps:**
1. Assess damage and identify recovery point
2. Provision new infrastructure if needed
3. Restore database from backup
4. Restore ChromaDB collections
5. Update DNS/load balancer settings
6. Verify all services are operational
7. Run validation suite
8. Resume normal operations

## Performance Tuning

### Database Optimization

1. **Index Management**
   ```sql
   -- Create indexes for common queries
   CREATE INDEX idx_entities_actor_created 
   ON memory_entities(actor_id, created_at DESC);
   
   CREATE INDEX idx_entities_type_grade 
   ON memory_entities(entity_type, grade DESC);
   
   -- Analyze table statistics
   ANALYZE memory_entities;
   ANALYZE memory_relationships;
   ```

2. **Query Optimization**
   ```sql
   -- Enable query plan logging
   SET log_min_duration_statement = 1000;  -- Log queries over 1 second
   
   -- Use EXPLAIN ANALYZE for slow queries
   EXPLAIN (ANALYZE, BUFFERS) 
   SELECT * FROM memory_entities 
   WHERE actor_id = 'client_123' 
   ORDER BY created_at DESC 
   LIMIT 100;
   ```

3. **Connection Pool Tuning**
   ```python
   # Optimal pool settings
   DATABASE_POOL_SIZE = 20
   DATABASE_MAX_OVERFLOW = 30
   DATABASE_POOL_TIMEOUT = 30
   DATABASE_POOL_RECYCLE = 3600
   ```

### API Performance

1. **Request Caching**
   ```python
   # Redis caching configuration
   CACHE_TTL = {
       "entity_search": 300,  # 5 minutes
       "entity_get": 3600,    # 1 hour
       "stats": 600           # 10 minutes
   }
   ```

2. **Rate Limiting**
   ```python
   # Rate limit configuration
   RATE_LIMITS = {
       "default": "100/minute",
       "search": "30/minute",
       "bulk_create": "10/minute"
   }
   ```

### ChromaDB Optimization

1. **Collection Management**
   ```python
   # Optimize collection settings
   collection_metadata = {
       "hnsw:space": "cosine",
       "hnsw:construction_ef": 200,
       "hnsw:search_ef": 100,
       "hnsw:M": 16
   }
   ```

2. **Batch Processing**
   ```python
   # Optimal batch sizes
   EMBEDDING_BATCH_SIZE = 100
   CHROMADB_BATCH_SIZE = 1000
   ```

## Maintenance Procedures

### Regular Maintenance Tasks

#### Daily
- [ ] Check system health status
- [ ] Review error logs
- [ ] Monitor disk space
- [ ] Verify backup completion

#### Weekly
- [ ] Run database VACUUM
- [ ] Update table statistics
- [ ] Review slow query log
- [ ] Check for unused indexes

#### Monthly
- [ ] Full system validation
- [ ] Performance baseline update
- [ ] Security patches
- [ ] Capacity planning review

### Database Maintenance

1. **Vacuum and Analyze**
   ```bash
   # Run vacuum analyze
   psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c "VACUUM ANALYZE;"
   
   # Check vacuum stats
   psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c "
   SELECT schemaname, tablename, last_vacuum, last_autovacuum
   FROM pg_stat_user_tables
   ORDER BY last_vacuum NULLS FIRST;"
   ```

2. **Index Maintenance**
   ```sql
   -- Rebuild bloated indexes
   REINDEX TABLE memory_entities;
   REINDEX TABLE memory_relationships;
   
   -- Find unused indexes
   SELECT schemaname, tablename, indexname, idx_scan
   FROM pg_stat_user_indexes
   WHERE idx_scan = 0
   AND indexname NOT LIKE '%_pkey';
   ```

### Log Rotation

```bash
# logrotate configuration
/var/log/memory-service/*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 0644 memory memory
    sharedscripts
    postrotate
        systemctl reload memory-service
    endscript
}
```

## Emergency Response

### Service Outage Response

1. **Immediate Actions (0-5 minutes)**
   - Check service status
   - Review recent deployments
   - Check system resources
   - Notify stakeholders

2. **Diagnosis (5-15 minutes)**
   - Review error logs
   - Check database connectivity
   - Verify external dependencies
   - Run health checks

3. **Recovery (15-60 minutes)**
   - Implement fix or rollback
   - Restart affected services
   - Verify functionality
   - Monitor for stability

### Incident Response Template

```markdown
## Incident Report

**Incident ID:** INC-YYYY-MM-DD-001
**Date/Time:** YYYY-MM-DD HH:MM UTC
**Severity:** Critical/High/Medium/Low
**Duration:** XX minutes

### Summary
Brief description of the incident

### Impact
- Services affected
- Number of users impacted
- Data loss (if any)

### Root Cause
Technical explanation of what caused the incident

### Timeline
- HH:MM - Incident detected
- HH:MM - Initial diagnosis
- HH:MM - Fix implemented
- HH:MM - Service restored
- HH:MM - Monitoring confirmed stability

### Action Items
- [ ] Immediate fixes applied
- [ ] Long-term solutions needed
- [ ] Process improvements

### Lessons Learned
What can be improved to prevent recurrence
```

### Escalation Matrix

| Severity | Response Time | Escalation Path | Notification |
|----------|---------------|-----------------|--------------|
| Critical | < 5 min | On-call → Team Lead → CTO | All stakeholders |
| High | < 15 min | On-call → Team Lead | Technical team |
| Medium | < 1 hour | On-call engineer | Team notification |
| Low | < 4 hours | Next business day | Email summary |

### Emergency Contacts

- **On-Call Engineer**: Check PagerDuty
- **Database Admin**: db-team@company.com
- **Infrastructure**: infra-team@company.com
- **Security Team**: security@company.com

## Appendix

### Useful Commands Reference

```bash
# Quick health check
curl -s http://localhost:8001/health | jq .

# Database connection test
pg_isready -h $DB_HOST -p $DB_PORT -U $DB_USER

# Service restart
systemctl restart memory-service

# Log tail
journalctl -u memory-service -f

# Resource check
htop -p $(pgrep -d, -f "memory-service|chroma")

# Network diagnostics
netstat -tuln | grep -E "8001|8443|8002|5432|8000"
```

### Configuration Files

- **Memory Service**: `/etc/memory-service/config.yaml`
- **Database**: `/etc/postgresql/15/main/postgresql.conf`
- **ChromaDB**: `/opt/chroma/config.yaml`
- **Nginx**: `/etc/nginx/sites-available/memory-api`

### Log Locations

- **Memory Service**: `/var/log/memory-service/`
- **PostgreSQL**: `/var/log/postgresql/`
- **ChromaDB**: `/var/log/chroma/`
- **System**: `journalctl -u memory-service`