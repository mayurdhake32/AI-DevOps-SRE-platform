# Error Classification Guide

## Classification Framework

### By System Layer

| Layer | Examples | Typical Response |
|-------|----------|------------------|
| Infrastructure | Disk full, network partition, node failure | Infrastructure team |
| Platform | Kubernetes pod crash, DNS failure | Platform/SRE team |
| Application | Null pointer, logic error, timeout | Development team |
| Database | Deadlock, slow query, replication lag | DBA team |
| External | Third-party API down, CDN issue | Vendor escalation |

### By Error Type

**Transient Errors (Retryable):**
- Network timeout
- Rate limiting (429)
- Database lock timeout
- **Action:** Implement exponential backoff retry

**Permanent Errors (Non-retryable):**
- Authentication failure (401/403)
- Invalid request (400)
- Resource not found (404)
- **Action:** Fail fast, log detailed context

**System Errors (Require intervention):**
- 500 Internal Server Error
- 502 Bad Gateway
- 503 Service Unavailable
- **Action:** Page on-call, begin incident response

## Root Cause Categories

### 1. Code Defect
**Indicators:**
- Stack trace points to specific function
- Error started after deployment
- Reproducible with specific input

**Examples:**
```
TypeError: Cannot read property 'id' of undefined
    at processOrder (/app/src/orders.js:42:15)
```

### 2. Configuration Error
**Indicators:**
- Error mentions missing env var
- Works in staging but not prod
- Recent config change

**Examples:**
```
Error: DATABASE_URL is not defined
Error: Invalid API key format
```

### 3. Resource Exhaustion
**Indicators:**
- OOMKilled, CPU throttling
- Connection pool exhausted
- Disk full errors

**Examples:**
```
FATAL: sorry, too many clients already
Error: ENOSPC: no space left on device
```

### 4. Dependency Failure
**Indicators:**
- Timeout connecting to external service
- Certificate errors
- DNS resolution failures

**Examples:**
```
Error: connect ETIMEDOUT 203.0.113.45:443
Error: certificate has expired
```

### 5. Data Corruption
**Indicators:**
- Checksum mismatches
- Unexpected null values in required fields
- Referential integrity violations

**Examples:**
```
IntegrityError: FOREIGN KEY constraint failed
Error: Invalid checksum for file data.bin
```

## Automated Classification Rules

```python
# Example classifier logic
def classify_error(log_entry):
    message = log_entry.get("message", "")

    if "timeout" in message.lower() or "ETIMEDOUT" in message:
        return {"category": "transient", "action": "retry"}

    if "OutOfMemory" in message or "OOMKilled" in message:
        return {"category": "resource_exhaustion", "action": "scale_up"}

    if "FATAL: remaining connection slots" in message:
        return {"category": "resource_exhaustion", "action": "kill_idle_connections"}

    if "NullPointerException" in message or "Cannot read property" in message:
        return {"category": "code_defect", "action": "deploy_fix"}

    if "certificate" in message.lower() or "SSL" in message:
        return {"category": "dependency_failure", "action": "check_certificates"}

    return {"category": "unknown", "action": "investigate"}
```

## Escalation Matrix

| Error Category | First Responder | Escalation If Not Resolved In |
|----------------|-----------------|------------------------------|
| Code Defect | Feature team | 1 hour → Engineering Manager |
| Config Error | SRE / DevOps | 30 min → Platform Lead |
| Resource Exhaustion | SRE | 15 min → Infrastructure |
| Dependency Failure | SRE | 30 min → Vendor support |
| Data Corruption | DBA + Feature team | Immediate → Engineering Director |
| Security Issue | Security team | Immediate → CISO |
