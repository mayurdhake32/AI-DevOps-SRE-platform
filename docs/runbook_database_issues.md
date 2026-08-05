# Runbook: Database Connection & Performance Issues

## Severity: P1 — Critical (if production DB), P2 — High (if read replica)

## Symptoms
- Application logs: `FATAL: sorry, too many clients already`
- Slow query alerts firing
- Replication lag increasing
- Disk usage > 85%

## Diagnosis Steps

### 1. Check Database Health
```bash
# Connect to database
kubectl exec -it postgres-primary-0 -- psql -U app_user -d production

# Check active connections
SELECT state, COUNT(*) FROM pg_stat_activity GROUP BY state;

# Check for blocked queries
SELECT blocked_locks.pid AS blocked_pid,
       blocked_activity.usename AS blocked_user,
       blocking_locks.pid AS blocking_pid,
       blocking_activity.usename AS blocking_user
FROM pg_catalog.pg_locks blocked_locks
JOIN pg_catalog.pg_stat_activity blocked_activity ON blocked_activity.pid = blocked_locks.pid
JOIN pg_catalog.pg_locks blocking_locks ON blocking_locks.locktype = blocked_locks.locktype
JOIN pg_catalog.pg_stat_activity blocking_activity ON blocking_activity.pid = blocking_locks.pid
WHERE NOT blocked_locks.granted;
```

### 2. Check Replication Status
```bash
# On primary
SELECT client_addr, state, sent_lsn, write_lsn, flush_lsn, replay_lsn 
FROM pg_stat_replication;

# On replica
SELECT EXTRACT(EPOCH FROM (now() - pg_last_xact_replay_timestamp())) AS lag_seconds;
```

## Fixes

### Too Many Connections
```bash
# Kill idle connections older than 1 hour
SELECT pg_terminate_backend(pid) FROM pg_stat_activity 
WHERE state = 'idle' AND state_change < NOW() - INTERVAL '1 hour';

# Increase max_connections (requires restart)
# Edit postgresql.conf: max_connections = 300
```

### Slow Queries
```sql
-- Find top 10 slow queries by total time
SELECT query, calls, total_exec_time, mean_exec_time 
FROM pg_stat_statements 
ORDER BY total_exec_time DESC 
LIMIT 10;

-- Add missing index (example)
CREATE INDEX CONCURRENTLY idx_orders_created_at ON orders(created_at);
```

### Disk Space Critical
```bash
# Check largest tables
SELECT schemaname, tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) 
FROM pg_tables ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC LIMIT 10;

# Vacuum large tables
VACUUM ANALYZE large_table;

# Archive old logs if applicable
```

## Prevention
- Set `max_connections` based on app server count × connection pool size
- Enable `pg_stat_statements` extension for query analysis
- Set up automatic VACUUM scheduling
- Monitor replication lag with alert threshold of 30 seconds
