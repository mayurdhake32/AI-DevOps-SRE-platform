# Incident Report Template

## INC-YYYY-MM-DD-XXX: [Brief Title]

### Metadata
- **Severity:** P1/P2/P3/P4
- **Status:** Resolved / Mitigated / Ongoing
- **Detection:** Automated alert / Manual report / Customer complaint
- **Start Time:** YYYY-MM-DD HH:MM UTC
- **End Time:** YYYY-MM-DD HH:MM UTC (or "Ongoing")
- **Duration:** X minutes/hours
- **Impact:** [Number of users affected, revenue impact, data loss]

### Timeline (All times UTC)

| Time | Event |
|------|-------|
| 14:30 | Monitoring alert fired: error rate > 10% |
| 14:32 | On-call engineer paged |
| 14:35 | Identified database connection pool exhaustion |
| 14:40 | Mitigated by restarting application pods |
| 14:45 | Error rate returned to normal |
| 15:00 | Root cause investigation started |

### Root Cause Analysis

**What happened:**
[Detailed description of the failure]

**Why it happened:**
[Technical root cause]

**Why we didn't catch it earlier:**
[Gap in monitoring/testing]

### Impact Assessment

- **Users affected:** ~12,000 (15% of active users)
- **Requests failed:** ~45,000
- **Data loss:** None / X records
- **Revenue impact:** $X
- **SLA impact:** 99.9% → 99.2% for the month

### Resolution Steps

1. [Step taken]
2. [Step taken]
3. [Step taken]

### Lessons Learned

**What went well:**
- [Positive aspect]

**What could be better:**
- [Area for improvement]

### Action Items

| ID | Action | Owner | Due Date | Status |
|----|--------|-------|----------|--------|
| 1 | Add connection pool monitoring | @sre-team | +7 days | Open |
| 2 | Implement circuit breaker | @backend-team | +14 days | Open |
| 3 | Update runbook with new RCA | @oncall | +2 days | Open |

### Related Links
- [Slack thread](#)
- [PagerDuty incident](#)
- [Grafana dashboard](#)
- [GitHub issue](#)
