# MongoDB Troubleshooting

## Connection Refused

### Fix
```bash
# Check if running
sudo systemctl status mongod

# Check bind IP
sudo cat /etc/mongod.conf | grep bindIp

# If bound to 127.0.0.1 only, change to 0.0.0.0 or specific IP
net:
  bindIp: 0.0.0.0
```

## Slow Queries

### Diagnosis
```javascript
// Find slow queries
db.currentOp({ "secs_running": { $gt: 5 }})

// Enable profiler
db.setProfilingLevel(1, { slowms: 100 })
db.system.profile.find().sort({ ts: -1 }).limit(5)
```

### Fix
1. Create indexes: `db.collection.createIndex({ field: 1 })`
2. Use covered queries (projection includes only indexed fields)
3. Check for missing indexes with `.explain("executionStats")`

## Replication Lag

```bash
# Check replica set status
rs.status()

# Check oplog window
rs.printReplicationInfo()
```

### Fix
1. Increase oplog size if too small
2. Add secondary nodes if read load is high
3. Check network between primary and secondaries

## WiredTiger Cache Pressure

```bash
# Check cache usage
mongostat

# In mongosh
db.serverStatus().wiredTiger.cache
```

### Fix
```yaml
# Adjust cache size (default is 50% RAM - 1GB)
storage:
  wiredTiger:
    engineConfig:
      cacheSizeGB: 4
```
