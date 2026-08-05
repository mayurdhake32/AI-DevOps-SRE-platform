# Log Analysis Guide for SREs

## Log Levels and What They Mean

| Level | Color | Action Required |
|-------|-------|----------------|
| ERROR | Red | Immediate investigation |
| WARN | Yellow | Monitor, investigate if pattern repeats |
| INFO | Blue | Normal operation |
| DEBUG | Gray | Only enable for troubleshooting |

## Common Log Patterns

### Memory Issues
```
java.lang.OutOfMemoryError: Java heap space
# → Increase heap size or fix memory leak

fatal error: runtime: out of memory
# → Go application exceeded limits

Killed process 12345 (python) total-vm:2097152kB, anon-rss:1048576kB
# → OOMKilled by kernel, increase container memory limit
```

### Database Issues
```
could not connect to server: Connection refused
# → Database is down or network issue

FATAL: remaining connection slots are reserved
# → Connection pool exhausted

ERROR: deadlock detected
# → Transaction ordering issue, retry logic needed
```

### Network Issues
```
connection timeout after 30000ms
# → Check firewall, DNS, or downstream service health

502 Bad Gateway
# → Upstream service unavailable

SSL handshake failed
# → Certificate expired or misconfigured
```

## Structured Logging Best Practices

### Good Log Format (JSON)
```json
{
  "timestamp": "2026-08-04T14:40:30Z",
  "level": "ERROR",
  "service": "payment-api",
  "trace_id": "abc123",
  "message": "Payment processing failed",
  "error": "insufficient_funds",
  "user_id": "user_456",
  "duration_ms": 245
}
```

### Querying Logs with Loki
```bash
# Find all errors for a service
{service="payment-api"} |= "ERROR"

# Find slow requests
{service="api-gateway"} | json | duration_ms > 1000

# Error rate over time
sum(rate({level="ERROR"}[5m])) by (service)
```

## Log Aggregation Setup

### Fluent Bit Configuration
```ini
[INPUT]
    Name tail
    Path /var/log/app/*.log
    Parser json
    Tag app.*

[OUTPUT]
    Name loki
    Match *
    Host loki.monitoring.svc.cluster.local
    Port 3100
    Labels job=app-logs
```

## Alerting Rules

```yaml
# Prometheus alert for error spike
- alert: HighErrorRate
  expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
  for: 2m
  labels:
    severity: critical
  annotations:
    summary: "High error rate detected"
```
