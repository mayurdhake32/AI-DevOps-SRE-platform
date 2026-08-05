# ArgoCD Troubleshooting

## Application OutOfSync

### Diagnosis
```bash
argocd app get <app-name>
kubectl describe application <app-name> -n argocd
```

### Fix
1. **Manual sync**: Click "Sync" in UI or `argocd app sync <app>`
2. **Auto-sync disabled**: Enable in app spec
3. **Resource hooks failing**: Check hook logs
4. **CRD not in Git**: Add CRD manifests to repo

## Sync Failed

### Error
```
ComparisonError: rpc error: code = Unknown desc = ...
```

### Fix
```bash
# Hard refresh
argocd app get <app> --hard-refresh

# Check repo access
argocd repo list

# Re-add repo if credentials expired
argocd repo add https://github.com/org/repo --username ... --password ...
```

## ArgoCD Server Not Accessible

```bash
# Port forward
kubectl port-forward svc/argocd-server -n argocd 8080:443

# Or check ingress
kubectl get ingress -n argocd
```

## Dex (SSO) Login Issues

### Fix
```bash
# Check dex config
kubectl get configmap argocd-cm -n argocd -o yaml

# Restart dex
kubectl rollout restart deployment dex-server -n argocd
```

## App of Apps Pattern Issues

```bash
# Parent app must be synced first
argocd app sync parent-app

# Then child apps will auto-create
argocd app list
```
