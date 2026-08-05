# Prometheus & Grafana Troubleshooting

## Prometheus Target Down

### Diagnosis
```bash
# Check target status
http://prometheus:9090/targets

# Check config
promtool check config /etc/prometheus/prometheus.yml

# Test scrape
curl http://target:9090/metrics
```

### Fixes
1. Verify target is running and metrics endpoint accessible
2. Check for network policies/firewalls blocking scrape
3. Ensure `job_name` and `targets` are correct in config
4. Check target's `/metrics` returns valid Prometheus format

## Grafana No Data

### Causes
- Wrong data source selected
- Time range doesn't contain data
- Query syntax error
- Prometheus retention expired data

### Fix
1. Test data source: Configuration → Data Sources → Test
2. Check query in Prometheus first: `http://prometheus:9090/graph`
3. Adjust time range to when data exists
4. Check Prometheus retention: `--storage.tsdb.retention.time=15d`

## High Cardinality

### Symptoms
- Prometheus memory usage growing
- Slow queries
- "too many time series" errors

### Fix
```promql
# Find high cardinality metrics
topk(10, count by (__name__)({__name__=~".+"}))

# Drop high cardinality labels in relabel config
metric_relabel_configs:
  - source_labels: [user_id]
    regex: '.+'
    target_label: user_id
    replacement: ''
```

## Alertmanager Not Firing

### Diagnosis
```bash
# Check alert status
http://prometheus:9090/alerts

# Check Alertmanager
http://alertmanager:9093

# Test alert
amtool check-config /etc/alertmanager/alertmanager.yml
```

### Common Fixes
1. Alert expression must return data (not just be valid)
2. `for:` duration must elapse before firing
3. Alertmanager route must match alert labels
4. Check inhibition rules aren't suppressing

## Recording Rules Slow

### Fix
```yaml
groups:
  - name: example
    interval: 30s  # Don't evaluate too frequently
    rules:
      - record: job:http_requests:rate5m
        expr: sum(rate(http_requests_total[5m])) by (job)
```
