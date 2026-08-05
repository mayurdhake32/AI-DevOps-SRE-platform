# Redis Troubleshooting

## Connection Issues

### Error
```
Redis::CannotConnectError: Error connecting to Redis on localhost:6379
```

### Fixes
```bash
# Check if running
redis-cli ping

# Check config
sudo cat /etc/redis/redis.conf | grep bind
sudo cat /etc/redis/redis.conf | grep port

# Restart
sudo systemctl restart redis
```

## Memory Full

### Diagnosis
```bash
redis-cli INFO memory
redis-cli --bigkeys
```

### Fixes
1. Set maxmemory policy: `allkeys-lru` or `allkeys-lfu`
2. Enable key expiration: `EXPIRE key 3600`
3. Shard data across multiple Redis instances
4. Use Redis Cluster for horizontal scaling

## High Latency

### Diagnosis
```bash
redis-cli --latency-history
redis-cli SLOWLOG GET 10
```

### Fixes
1. Avoid O(N) commands on large keys: `KEYS`, `SMEMBERS`, `HGETALL`
2. Use `SCAN` instead of `KEYS`
3. Pipeline multiple commands
4. Check for blocking operations: `BLPOP` with timeout

## Replication Lag

```bash
# Check replication info
redis-cli INFO replication

# If lag is high
redis-cli CONFIG SET repl-backlog-size 256mb
```

## Persistence Issues

### RDB Save Failed
```bash
# Check disk space
df -h

# Check permissions on /var/lib/redis
ls -la /var/lib/redis

# Force save
redis-cli BGSAVE
```
