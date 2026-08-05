# Helm & Kubernetes Troubleshooting

## Helm Release Failed

### Diagnosis
```bash
helm history <release> -n <namespace>
helm status <release> -n <namespace>
helm get values <release> -n <namespace>
```

### Fix
```bash
# Rollback
helm rollback <release> <revision> -n <namespace>

# Debug template rendering
helm template <chart> --debug

# Upgrade with debug
helm upgrade <release> <chart> --debug --dry-run
```

## Helm Repo Issues

```bash
# Update repos
helm repo update

# Add repo
helm repo add stable https://charts.helm.sh/stable

# Search
helm search repo nginx
```

## CRD Conflicts

### Error
```
Error: Unable to continue with install: CustomResourceDefinition ... already exists
```

### Fix
```bash
# Skip CRDs if already exist
helm install <release> <chart> --skip-tests

# Or manually manage CRDs
kubectl apply -f crds/
helm install <release> <chart> --no-hooks
```

## Values Not Applied

### Fix
```bash
# Check values are merged correctly
helm get values <release> --all

# Override with --set
helm upgrade <release> <chart> --set replicaCount=3

# Use values file
helm upgrade <release> <chart> -f custom-values.yaml
```

## Helm Hook Failures

```bash
# Check hook status
kubectl get jobs -n <namespace>

# Delete failed hook manually
kubectl delete job <hook-name> -n <namespace>

# Re-run release
helm upgrade <release> <chart>
```
