# Monitoring & Alerting Guide

## The Four Golden Signals

### 1. Latency
```yaml
# Prometheus recording rule
- record: job:http_request_duration_seconds:mean5m
  expr: rate(http_request_duration_seconds_sum[5m]) / rate(http_request_duration_seconds_count[5m])

# Alert
- alert: HighLatency
  expr: histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[5m])) > 2
  for: 5m
  labels:
    severity: warning
```

### 2. Traffic
```yaml
- alert: LowTraffic
  expr: rate(http_requests_total[5m]) < 10
  for: 10m
  labels:
    severity: warning
```

### 3. Errors
```yaml
- alert: HighErrorRate
  expr: |
    (
      sum(rate(http_requests_total{status=~"5.."}[5m])) by (service)
      /
      sum(rate(http_requests_total[5m])) by (service)
    ) > 0.01
  for: 2m
  labels:
    severity: critical
```

### 4. Saturation
```yaml
- alert: HighCPU
  expr: 100 - (avg by (instance) (irate(node_cpu_seconds_total{mode="idle"}[5m])) * 100) > 80
  for: 10m
  labels:
    severity: warning
```

## Alert Severity Definitions

| Severity | Response Time | Example |
|----------|--------------|---------|
| P1 (Critical) | < 5 minutes | Service down, data loss, security breach |
| P2 (High) | < 30 minutes | Degraded performance, partial outage |
| P3 (Medium) | < 4 hours | Non-critical feature broken |
| P4 (Low) | Next business day | Cleanup tasks, minor issues |

## Alert Fatigue Prevention

**Bad Alert:**
```
"CPU usage > 80%" → Fires every night during backup
```

**Good Alert:**
```
"CPU usage > 80% AND NOT time() % 86400 between 72000 and 79200" 
# Excludes backup window (8pm-10pm UTC)
```

## Dashboard Best Practices

### RED Dashboard (for each service)
- **R**equest rate
- **E**rror rate  
- **D**uration (latency)

### USE Dashboard (for each resource)
- **U**tilization
- **S**aturation
- **E**rrors

## SLO/SLI Definitions

```yaml
# Example SLO: 99.9% availability over 30 days
SLI: successful_requests / total_requests
SLO: 0.999
Error_budget: 1 - 0.999 = 0.001 (43 minutes downtime/month)
```

## On-Call Rotation
- Primary: Week 1
- Secondary: Week 2
- Shadow: New team members
- Escalation: Engineering Manager after 30 min no response
