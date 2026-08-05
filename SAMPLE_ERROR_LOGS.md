# Sample Error Logs for Testing

Copy any of these and paste into the AI Analysis form or API.

---

## Kubernetes — CrashLoopBackOff

```
Back-off restarting failed container
Error from server (BadRequest): container "payment-api" in pod "payment-api-7c9b4f5d8-x2k4m" is waiting to start: CrashLoopBackOff
Last State: Terminated with exit code 1
Reason: Error
```

**Expected category:** kubernetes

---

## Kubernetes — ImagePullBackOff

```
Failed to pull image "myregistry/app:v2.1": rpc error: code = Unknown desc = Error response from daemon: manifest unknown
Pod status: ImagePullBackOff
Events: Failed to pull image "myregistry/app:v2.1": manifest unknown
```

**Expected category:** kubernetes, docker

---

## Kubernetes — OOMKilled

```
OOMKilled: Container exceeded its memory limit
Usage: 512Mi, Limit: 256Mi, Request: 128Mi
Container ID: docker://7a8b9c2d3e4f
Restart Count: 15
```

**Expected category:** kubernetes, resource

---

## Docker — Daemon Not Running

```
Cannot connect to the Docker daemon at unix:///var/run/docker.sock. Is the docker daemon running?
Got permission denied while trying to connect to the Docker daemon socket at unix:///var/run/docker.sock
```

**Expected category:** docker, permission

---

## Docker — Pull Access Denied

```
Error response from daemon: pull access denied for myapp, repository does not exist or may require 'docker login'
docker: Error response from daemon: unauthorized: authentication required
```

**Expected category:** docker, permission

---

## Docker — Build Fail

```
failed to solve: rpc error: code = Unknown desc = failed to solve with frontend dockerfile.v0: failed to read dockerfile
ERROR: failed to solve: failed to read dockerfile: open /var/lib/docker/tmp/.../Dockerfile: no such file or directory
```

**Expected category:** docker, syntax

---

## Database — Connection Pool Exhausted

```
FATAL: sorry, too many clients already
PostgreSQL connection pool exhausted: 100/100 connections in use
ConnectionPoolTimeout: Unable to get connection from pool after 30000ms
```

**Expected category:** resource, docker

---

## Terraform — State Lock

```
Error: Error acquiring the state lock: ConditionalCheckFailedException: The conditional request failed
State lock already held by workspace/lock
Lock Info: ID: 12345, Path: terraform.tfstate, Who: user@hostname, Created: 2026-08-05
```

**Expected category:** terraform

---

## Terraform — Provider Config Missing

```
Error: Provider configuration not present
To work with aws_instance.web its original provider configuration at provider["registry.terraform.io/hashicorp/aws"] is required, but no provider configuration block was found.
```

**Expected category:** terraform

---

## YAML — Indentation Error

```
yaml.scanner.ScannerError: mapping values are not allowed here in "docker-compose.yml", line 15, column 18
Error: YAMLException: bad indentation of a mapping entry at line 23, column 5
```

**Expected category:** yaml, syntax

---

## AWS — S3 Access Denied

```
AccessDenied: Access Denied
status code: 403, request id: ABC123, host id: xyz
User: arn:aws:iam::123456789:user/ci-cd is not authorized to perform: s3:PutObject on resource: "arn:aws:s3:::artifacts/*"
```

**Expected category:** permission

---

## AWS — EC2 Unreachable

```
SSH connection timeout to ec2-203-0-113-45.compute-1.amazonaws.com
Instance Status Checks: failed
System Status Checks: passed
Connection timed out during banner exchange
```

**Expected category:** network

---

## Nginx — 502 Bad Gateway

```
502 Bad Gateway
nginx/1.24.0
upstream prematurely closed connection while reading response header from upstream
upstream: "http://10.0.1.5:8080"
```

**Expected category:** network, kubernetes

---

## Nginx — SSL Certificate Expired

```
SSL: error:14094418:SSL routines:ssl3_read_bytes:tlsv1 alert unknown ca
curl: (60) SSL certificate problem: certificate has expired
certificate has expired: certificate verify failed
```

**Expected category:** network

---

## Redis — Connection Refused

```
Redis::CannotConnectError: Error connecting to Redis on localhost:6379 (Errno::ECONNREFUSED)
Connection refused - connect(2) for "localhost" port 6379
```

**Expected category:** network

---

## Redis — Memory Full

```
OOM command not allowed when used memory > 'maxmemory'
MISCONF Redis is configured to save RDB snapshots, but it is currently not able to persist on disk
```

**Expected category:** resource

---

## Jenkins — Build Hang

```
Build #456 is running for 2 hours 30 minutes
Still waiting to schedule task — All nodes are offline
Waiting for next available executor
Pipeline input: Proceed or Abort?
```

**Expected category:** unknown

---

## GitHub Actions — Permission Denied

```
Error: Resource not accessible by integration
GitHub Actions: Unable to get ACTIONS_ID_TOKEN_REQUEST_URL env variable
Error: Input required and not supplied: GITHUB_TOKEN
```

**Expected category:** permission

---

## Prometheus — Target Down

```
Get "http://10.0.2.15:9090/metrics": connection refused
target "node-exporter:9100" is down
last error: "context deadline exceeded"
```

**Expected category:** network

---

## Git — Merge Conflict

```
Auto-merging src/app.py
CONFLICT (content): Merge conflict in src/app.py
Automatic merge failed; fix conflicts and then commit the result.
```

**Expected category:** syntax

---

## Elasticsearch — Red Cluster

```
cluster health: red
unassigned_shards: 3
relocating_shards: 0
active_shards_percent_as_number: 85.0
```

**Expected category:** resource

---

## Helm — Release Failed

```
Error: UPGRADE FAILED: cannot patch "payment-api" with kind Deployment: Operation cannot be fulfilled on deployments.apps "payment-api": the object has been modified; please apply your changes to the latest version and try again
```

**Expected category:** kubernetes

---

## ArgoCD — OutOfSync

```
ComparisonError: rpc error: code = Unknown desc = Manifest generation error (cached): `helm template . --name-template payment-api` failed exit status 1: Error: failed to download "stable/nginx-ingress" at version "1.0.0"
```

**Expected category:** kubernetes

---

## Linux — Disk Full

```
No space left on device
write /var/lib/docker/tmp/...: no space left on device
df: no file systems processed
ENOSPC: no space left on device, write
```

**Expected category:** resource, docker

---

## Linux — High CPU

```
load average: 15.23, 12.45, 8.90
CPU usage: 98.5% user, 1.2% system, 0.3% idle
ksoftirqd/0 using 99.8% CPU
```

**Expected category:** resource

---

## Microservices — Circuit Breaker

```
CircuitBreaker 'payment-service' is OPEN and does not permit further calls
Fallback method executed for getPaymentStatus
HystrixRuntimeException: payment-service failed and no fallback available
```

**Expected category:** network

---

## SSL — Certificate Expired

```
curl: (60) SSL certificate problem: certificate has expired
certificate verify failed: certificate has expired
X509_V_ERR_CERT_HAS_EXPIRED
```

**Expected category:** network

---

## MongoDB — Slow Query

```
MongoError: operation exceeded time limit
Query targeting: ns.payment.orders { status: "pending" } planSummary: COLLSCAN
Duration: 45230ms
```

**Expected category:** resource

---

## How to Use These for Testing

### Option 1: Streamlit UI
1. Open `http://localhost:8501`
2. Go to **AI Analysis**
3. Paste any log above
4. Click **Run AI Analysis**

### Option 2: API Directly
```python
import requests

log = "YOUR ERROR LOG HERE"

r = requests.post("http://localhost:8000/analyze", json={
    "log_content": log,
    "repo_name": "test-repo"
})
print(r.json())
```

### Option 3: Knowledge Base Search
```
http://localhost:8000/knowledge-base/search?query=CrashLoopBackOff&top_k=3
```

---

## Expected Results

| Error Log | Expected Primary Category | Expected Confidence |
|-----------|--------------------------|---------------------|
| CrashLoopBackOff | kubernetes | >0.7 |
| Docker daemon | docker | >0.7 |
| S3 Access Denied | permission | >0.6 |
| Terraform state lock | terraform | >0.7 |
| YAML indentation | yaml | >0.7 |
| Disk full | resource | >0.6 |
| SSL expired | network | >0.6 |
| Redis OOM | resource | >0.6 |
