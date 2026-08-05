# CI/CD Pipeline Failure Runbook

## Build Failures

### Docker Build Fails
```bash
# Common errors and fixes

# 1. "no space left on device"
docker system prune -a --volumes  # WARNING: removes unused images
# Or: Increase runner disk size

# 2. "executor failed running [/bin/sh -c pip install...]"
# → Check requirements.txt for conflicting dependencies
pip install -r requirements.txt --dry-run

# 3. Multi-stage build context too large
# → Add .dockerignore file
cat > .dockerignore << EOF
.git
node_modules
__pycache__
*.pyc
.env
EOF
```

### Test Failures
```bash
# Re-run failed tests locally
docker-compose -f docker-compose.test.yml up --abort-on-container-exit

# Check for flaky tests
pytest --count=10 tests/test_flaky.py  # Run 10 times

# Common causes:
# - Race conditions in async tests
# - Database state leaking between tests
# - External service dependencies not mocked
```

## Deployment Failures

### Helm Release Failed
```bash
# Check what went wrong
helm history <release> -n <namespace>
helm status <release> -n <namespace>

# Rollback
helm rollback <release> <revision> -n <namespace>

# Debug template rendering
helm template <chart> --debug > rendered.yaml
```

### ArgoCD Sync Failures
```bash
# Check application status
argocd app get <app-name>

# Common issues:
# 1. Resource quota exceeded → Request more resources
# 2. CRD not installed → Install CRD first
# 3. Image pull secret missing → Check registry credentials
```

## GitOps Issues

### Flux Reconciliation Failed
```bash
flux get kustomizations --watch

# Check source
flux get sources git

# Force reconciliation
flux reconcile source git <name>
flux reconcile kustomization <name>
```

## Prevention Checklist
- [ ] All tests pass before merge (branch protection rules)
- [ ] Docker images scanned for vulnerabilities (Trivy/Snyk)
- [ ] Resource limits set in all deployments
- [ ] Health checks configured
- [ ] Rollback tested in staging environment
