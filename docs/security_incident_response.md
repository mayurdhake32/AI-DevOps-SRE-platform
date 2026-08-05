# Security Incident Response Runbook

## Severity Levels

### Critical (SEV-1)
- Active data breach
- Ransomware attack
- Unauthorized admin access
- **Response:** All hands, immediate containment

### High (SEV-2)
- Vulnerability exploited in the wild
- Credential leak detected
- DDoS attack overwhelming defenses
- **Response:** Security team + on-call SRE

### Medium (SEV-3)
- Vulnerability scan findings
- Suspicious login patterns
- Policy violation
- **Response:** Security team within 4 hours

## Immediate Response (First 15 Minutes)

### 1. Contain
```bash
# Isolate compromised pod/node
kubectl cordon <node-name>
kubectl taint nodes <node-name> security=incident:NoSchedule

# Revoke compromised credentials
aws iam update-access-key --access-key-id <key> --status Inactive --user-name <user>
# Or rotate Kubernetes service account token
```

### 2. Preserve Evidence
```bash
# Capture pod state before termination
kubectl get pod <compromised-pod> -o yaml > incident-pod-$(date +%s).yaml
kubectl logs <compromised-pod> --all-containers > incident-logs-$(date +%s).log

# Snapshot disk if persistent volume
# (Cloud provider specific)
```

### 3. Notify
- Security team Slack: #security-incidents
- Engineering manager
- Legal/Compliance (if data involved)
- Customers (if required by SLA/regulations)

## Investigation Checklist

- [ ] **Scope:** What systems/data were accessed?
- [ ] **Entry Point:** How did attacker get in?
- [ ] **Timeline:** When did intrusion begin?
- [ ] **Impact:** What data was exfiltrated/modified?
- [ ] **Persistence:** Are there backdoors/backdoor accounts?
- [ ] **Lateral Movement:** Did attacker move to other systems?

## Common Attack Patterns

### Container Escape
**Indicators:**
- Privileged container running
- Host namespace access
- Suspicious host-level processes

**Response:**
```bash
# Check for privileged pods
kubectl get pods --all-namespaces -o json | jq '.items[] | select(.spec.containers[].securityContext.privileged==true) | .metadata.name'

# Remove privilege
kubectl patch deployment <name> --type=json -p='[{"op": "remove", "path": "/spec/template/spec/containers/0/securityContext/privileged"}]'
```

### Cryptomining
**Indicators:**
- High CPU from unknown process
- Connections to mining pools
- New containers with suspicious images

**Response:**
```bash
# Find high CPU pods
kubectl top pods --all-namespaces | sort -k3 -nr | head -10

# Check image signatures
# Remove unauthorized workloads
kubectl delete pod <suspicious-pod> --force
```

### Secret Leak
**Indicators:**
- Credentials in logs
- Exposed environment variables
- Unauthorized API calls

**Response:**
1. Rotate all potentially exposed secrets
2. Check audit logs for unauthorized access
3. Review Git history for accidental commits

## Post-Incident

- [ ] Full forensic analysis completed
- [ ] All backdoors removed
- [ ] All credentials rotated
- [ ] Monitoring/alerting gaps addressed
- [ ] Post-mortem written within 72 hours
- [ ] Regulatory notifications sent if required
- [ ] Insurance claim filed if applicable
