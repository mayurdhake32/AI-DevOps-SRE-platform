# Kubernetes Troubleshooting Guide

## Pod Stuck in Pending

### Diagnosis
```bash
kubectl describe pod <pod-name>
# Look for: Events section at the bottom
```

### Common Causes & Fixes

**Insufficient Resources:**
```bash
# Check node resources
kubectl top nodes
kubectl describe nodes | grep -A 5 "Allocated resources"

# Fix: Scale cluster or reduce resource requests
kubectl patch deployment <name> -p '{"spec":{"template":{"spec":{"containers":[{"name":"app","resources":{"requests":{"cpu":"100m","memory":"128Mi"}}}]}}}}'
```

**PVC Not Bound:**
```bash
kubectl get pvc
# If Pending, check storage class exists
kubectl get storageclass
```

**Taints/Tolerations Mismatch:**
Check if node has taints that pod doesn't tolerate.

## Pod CrashLoopBackOff

### Diagnosis
```bash
kubectl logs <pod-name> --previous
kubectl describe pod <pod-name> | grep -A 10 "Events"
```

### Common Causes
1. **Application crashing on startup** → Fix code/config
2. **Liveness probe failing** → Adjust probe settings or fix app
3. **Missing environment variables** → Check ConfigMap/Secrets
4. **Permission denied** → Check securityContext and file permissions

### Fix Example (Missing Env Var)
```bash
# Check if secret exists
kubectl get secret db-credentials

# If missing, recreate
kubectl create secret generic db-credentials   --from-literal=password=<value>   --from-literal=username=app_user
```

## High Memory Usage

```bash
# Find top memory consumers
kubectl top pods --all-namespaces | sort -k3 -nr | head -20

# Check for memory leaks
kubectl logs <pod> | grep -i "memory\|heap\|oom"

# Set memory limits if not set
kubectl set resources deployment <name> --limits=memory=512Mi
```

## DNS Resolution Issues

```bash
# Test DNS from inside pod
kubectl run -it --rm debug --image=busybox:1.28 --restart=Never -- nslookup kubernetes.default

# Check CoreDNS pods
kubectl get pods -n kube-system -l k8s-app=kube-dns
kubectl logs -n kube-system -l k8s-app=kube-dns

# Restart CoreDNS if needed
kubectl rollout restart deployment coredns -n kube-system
```

## Node NotReady

```bash
# Check node status
kubectl describe node <node-name>

# Common fixes
# 1. Disk pressure → Clean up images/logs
# 2. Memory pressure → Evict pods or add memory
# 3. PID pressure → Check for zombie processes
# 4. Kubelet down → SSH to node, restart kubelet
```
