# Runbook: HTTP 500 Internal Server Errors

## Severity: P1 — Critical

## Symptoms
- Users reporting "Something went wrong" pages
- 5xx errors spiking in monitoring dashboards
- Application logs showing unhandled exceptions

## Immediate Response (First 5 Minutes)

### 1. Check Error Rate
```bash
# Check error rate in last 5 minutes
curl -s "http://prometheus:9090/api/v1/query?query=rate(http_requests_total{status=~"5.."}[5m])"
```
**Threshold:** > 5% of total requests = page on-call engineer immediately.

### 2. Identify Affected Service
Check which microservice is throwing 500s:
- Look at `service` label in Prometheus metrics
- Check load balancer logs for upstream failures
- Review recent deployments: `kubectl rollout history deployment/<service>`

### 3. Check Application Logs
```bash
# Get recent error logs
kubectl logs -l app=<service-name> --tail=100 | grep ERROR

# Or with stern for multiple pods
stern <service-name> | grep -i error
```

## Common Root Causes

### Database Connection Pool Exhaustion
**Symptoms:** `ConnectionPoolTimeout`, `too many connections`
**Fix:**
```bash
# Check current connections
kubectl exec -it <db-pod> -- psql -c "SELECT count(*) FROM pg_stat_activity;"

# Restart affected pods (temporary relief)
kubectl rollout restart deployment/<service>

# Permanent fix: Increase pool size in config or add read replicas
```

### Null Pointer / Unhandled Exception
**Symptoms:** Stack trace in logs pointing to specific line
**Fix:**
1. Identify the commit that introduced the bug
2. Check if rollback is safe: `kubectl rollout undo deployment/<service>`
3. If rollback not possible, deploy hotfix

### Memory Leak Leading to OOMKills
**Symptoms:** Pods restarting, `OOMKilled` status, memory graph climbing
**Fix:**
```bash
# Check pod status
kubectl get pods -o wide | grep OOMKilled

# Temporary: Increase memory limit
kubectl patch deployment <service> -p '{"spec":{"template":{"spec":{"containers":[{"name":"app","resources":{"limits":{"memory":"2Gi"}}}]}}}}'
```

## Rollback Procedure
If issue started after deployment:
```bash
# Check last deployment
kubectl rollout history deployment/<service>

# Rollback to previous version
kubectl rollout undo deployment/<service>

# Verify rollback
kubectl get pods -w
```

## Post-Incident Actions
- [ ] Update this runbook if new root cause found
- [ ] Add monitoring alert for the specific error pattern
- [ ] Schedule post-mortem within 24 hours
- [ ] Create ticket for permanent fix

## Escalation
- If error rate > 50% for > 10 minutes → Escalate to Engineering Manager
- If database corruption suspected → Escalate to DBA team immediately
- If security-related (e.g., SQL injection causing crash) → Page Security team
