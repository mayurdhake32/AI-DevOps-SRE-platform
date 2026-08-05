# Production Deployment Checklist

## Pre-Deployment

- [ ] **Code Review:** PR approved by at least 1 senior engineer
- [ ] **Tests Passing:** Unit, integration, and E2E tests all green
- [ ] **Security Scan:** No CRITICAL or HIGH vulnerabilities (Trivy/Snyk)
- [ ] **Database Migrations:** Reviewed and tested in staging
- [ ] **Feature Flags:** New features behind flags, ready to toggle
- [ ] **Rollback Plan:** Previous version tagged and ready to deploy
- [ ] **Capacity Check:** Current resource usage < 70% of cluster capacity
- [ ] **Dependencies:** All downstream services healthy

## Deployment Steps

### 1. Staging Verification
```bash
# Deploy to staging first
kubectl apply -f k8s/staging/

# Run smoke tests
pytest tests/smoke/ -v

# Check for errors
kubectl logs -l app=<service> --tail=50 | grep ERROR
```

### 2. Canary Deployment
```bash
# Deploy to 10% of traffic
kubectl patch deployment <service> -p '{"spec":{"template":{"spec":{"containers":[{"name":"app","image":"<new-image>:<tag>"}]}}}}'

# Monitor for 15 minutes
# - Error rate < 1%
# - P99 latency < baseline + 20%
# - No increase in 5xx errors
```

### 3. Full Rollout
```bash
# If canary healthy, rollout to 100%
kubectl rollout status deployment/<service>

# Verify all pods running new version
kubectl get pods -l app=<service> -o jsonpath='{range .items[*]}{.spec.containers[0].image}{"\n"}{end}' | sort | uniq -c
```

## Post-Deployment

- [ ] **Smoke Tests:** Run against production
- [ ] **Monitoring:** Check dashboards for 30 minutes
- [ ] **Alerts:** Confirm no new alerts firing
- [ ] **Customer-Facing:** Check error tracking (Sentry)
- [ ] **Performance:** Compare before/after metrics
- [ ] **Rollback Window:** Keep rollback ready for 2 hours

## Emergency Rollback

```bash
# Immediate rollback
kubectl rollout undo deployment/<service>

# Or with Helm
helm rollback <release> <previous-revision>

# Verify rollback
kubectl get pods -w
```

## Communication

| Stage | Channel | Message |
|-------|---------|---------|
| Start | #deployments | "Deploying v1.2.3 to prod" |
| Success | #deployments | "v1.2.3 deployed successfully" |
| Issue | #incidents | "Rollback initiated for v1.2.3 — investigating" |
| Resolved | #incidents | "Issue resolved, root cause: [brief]" |
