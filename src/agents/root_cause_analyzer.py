"""
Root Cause Analysis Agent
=========================
Analyzes infrastructure/application errors using LLM + Knowledge Base.
FORCES verbose, detailed output via prompt engineering + retry loops + rich heuristics.
"""

import os
import json
import re
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum
from src.parsers.log_parser import ParsedLog
from src.rag.knowledge_base import DevOpsKnowledgeBase
from src.ml.training.error_classifier import ErrorClassifier
from src.utils.logger import get_logger

logger = get_logger(__name__)


class RootCauseCategory(Enum):
    CONFIGURATION_ERROR = "configuration_error"
    DEPENDENCY_ISSUE = "dependency_issue"
    RESOURCE_CONSTRAINT = "resource_constraint"
    PERMISSION_ISSUE = "permission_issue"
    NETWORK_ISSUE = "network_issue"
    CODE_BUG = "code_bug"
    INFRASTRUCTURE_FAILURE = "infrastructure_failure"
    EXTERNAL_DEPENDENCY = "external_dependency"
    UNKNOWN = "unknown"


@dataclass
class RootCause:
    category: RootCauseCategory
    description: str
    confidence: float
    affected_components: List[str]
    evidence: List[str]
    suggested_fixes: List[Dict]
    references: List[str]
    severity: str


class RootCauseAnalyzer:
    # ─────────────────────────────────────────────────────────────
    # ENHANCED SYSTEM PROMPT — forces verbose, technical output
    # ─────────────────────────────────────────────────────────────
    SYSTEM_PROMPT = """You are an elite Site Reliability Engineer (SRE) with 12+ years managing production systems at hyperscale (Kubernetes, AWS, GCP, Azure).

Your job is to perform a DEEP, VERBOSE root cause analysis. NEVER give one-line summaries or vague statements like "Kubernetes deployment failure."
Every field must be thorough, technical, and actionable.

## Response Format (STRICT JSON)
Return ONLY a valid JSON object with these exact keys:
{
  "category": "One of: configuration_error | dependency_issue | resource_constraint | permission_issue | network_issue | code_bug | infrastructure_failure | external_dependency | unknown",
  "description": "<DETAILED EXPLANATION — MINIMUM 250 WORDS. Be exhaustive.>",
  "confidence": <float 0.0-1.0>,
  "affected_components": ["<component 1>", "<component 2>"],
  "evidence": ["<log line 1>", "<log line 2>"],
  "suggested_fixes": [
    {"description": "<fix 1>", "priority": "critical|high|medium|low", "automation_possible": true|false},
    {"description": "<fix 2>", "priority": "...", "automation_possible": ...}
  ],
  "severity": "critical|high|medium|low",
  "prevention": "<DETAILED PREVENTION — MINIMUM 3 SENTENCES>",
  "analysis_steps": [
    {"step": "Log Parsing", "status": "Success", "detail": "..."},
    {"step": "Error Classification", "status": "Success", "detail": "..."},
    {"step": "Root Cause Analysis", "status": "Success", "detail": "..."},
    {"step": "Fix Generation", "status": "Success", "detail": "..."}
  ]
}

## CRITICAL RULES for the "description" field:
1. Identify the EXACT component that failed (pod name, container, node, service, DB table, etc.).
2. Explain the UNDERLYING MECHANISM — why did this specific error manifest? (e.g., "The kubelet's backoff manager increments restart delays exponentially because the container's entrypoint exits immediately...").
3. Trace the FAILURE CHAIN: what event triggered what, and how did it cascade?
4. Include TECHNICAL DETAILS: exit codes, signal numbers, resource metrics, API versions, config paths.
5. Mention SIMILAR SCENARIOS so the operator knows what else to check.
6. Use precise terminology. Do NOT say "something failed." Say "the liveness probe on port 8080/tcp failed because the JVM heap exceeded limits, causing GC thrashing..."

## CRITICAL RULES for "suggested_fixes":
- Provide 4–8 specific, ordered fixes.
- Include exact CLI commands where applicable (kubectl, docker, curl, SQL, etc.).
- Prioritize immediate mitigation first, then permanent resolution.

## CRITICAL RULES for "prevention":
- Provide CI/CD, monitoring, and architectural recommendations.
- Mention specific tools (Prometheus alerts, OPA policies, Helm hooks, etc.).

PENALTY: If your description is under 200 words, your analysis is INCOMPLETE and UNACCEPTABLE for production SRE work.
"""

    def __init__(self, knowledge_base: DevOpsKnowledgeBase,
                 error_classifier: ErrorClassifier, llm_provider: str = "openai"):
        self.kb = knowledge_base
        self.classifier = error_classifier
        self.llm_provider = llm_provider
        self._init_llm()

    def _init_llm(self):
        """Initialize LLM client - supports xAI (Grok), OpenAI, or local."""
        api_key = os.getenv("XAI_API_KEY") or os.getenv("OPENAI_API_KEY")
        base_url = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1")
        model = os.getenv("LLM_MODEL", "gpt-4")

        if not api_key:
            logger.warning("No API key found. Set XAI_API_KEY or OPENAI_API_KEY in .env file. Using heuristic analysis.")
            self.client = None
            return

        try:
            import openai
            self.client = openai.OpenAI(api_key=api_key, base_url=base_url)
            self.model = model
            logger.info(f"LLM initialized: {self.model} via {base_url}")
        except ImportError:
            logger.warning("OpenAI SDK not installed. Using heuristic analysis.")
            self.client = None

    # ─────────────────────────────────────────────────────────────
    # PUBLIC API
    # ─────────────────────────────────────────────────────────────

    def analyze(self, parsed_log: ParsedLog, repo_context: Optional[Dict] = None) -> RootCause:
        logger.info(f"Starting RCA for job: {parsed_log.job_name}")
        ml_prediction = self.classifier.predict(parsed_log.raw_log[:5000])
        primary_error_type = ml_prediction['primary_category']

        rag_context = ""
        if parsed_log.errors:
            main_error = parsed_log.errors[0]
            rag_context = self.kb.get_context_for_error(
                error_type=main_error['type'],
                error_message=main_error['message'], top_k=3
            )

        if self.client:
            root_cause = self._llm_analysis(parsed_log, ml_prediction, rag_context, repo_context)
        else:
            root_cause = self._heuristic_analysis(parsed_log, ml_prediction, rag_context)

        logger.info(f"RCA complete: {root_cause.category.value} (confidence: {root_cause.confidence})")
        return root_cause

    # ─────────────────────────────────────────────────────────────
    # LLM ANALYSIS WITH ENFORCEMENT
    # ─────────────────────────────────────────────────────────────

    def _llm_analysis(self, parsed_log: ParsedLog, ml_prediction: Dict,
                     rag_context: str, repo_context: Optional[Dict]) -> RootCause:
        prompt = self._build_analysis_prompt(parsed_log, ml_prediction, rag_context, repo_context)

        # Call LLM with retry enforcement for length
        raw_response = self._call_llm_with_enforcement(
            system_prompt=self.SYSTEM_PROMPT,
            user_prompt=prompt,
            min_description_words=200,
            max_retries=2
        )

        parsed = self._safe_parse_json(raw_response)

        # Post-process: if still too short, overlay rich heuristic content
        parsed = self._enforce_richness(parsed, parsed_log, ml_prediction, rag_context)

        return self._dict_to_root_cause(parsed, parsed_log)

    def _call_llm_with_enforcement(self, system_prompt: str, user_prompt: str,
                                   min_description_words: int = 200, max_retries: int = 2) -> str:
        """Calls LLM. If response is too short, retries with a critical feedback nudge."""
        raw_response = self._invoke_llm(system_prompt, user_prompt)

        for attempt in range(max_retries):
            parsed = self._safe_parse_json(raw_response)
            desc = parsed.get("description", "")
            word_count = len(desc.split())

            if word_count >= min_description_words:
                logger.info(f"[Analyzer] LLM response sufficient ({word_count} words)")
                return raw_response

            logger.warning(f"[Analyzer] Response too short ({word_count} words). Retry {attempt + 1}/{max_retries}")

            nudge = f"""


### CRITICAL FEEDBACK
Your previous response was only {word_count} words. This is UNACCEPTABLE for production SRE work.
You MUST expand the "description" field to at least {min_description_words} words.
Add more technical depth: discuss the exact subsystem, failure mode, cascading effects, and diagnostic reasoning.
Do NOT summarize. Be exhaustive. Include CLI commands, exit codes, and specific component names.
"""
            raw_response = self._invoke_llm(system_prompt, user_prompt + nudge)

        return raw_response

    def _invoke_llm(self, system_prompt: str, user_prompt: str) -> str:
        """Wrapper around the LLM client."""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.2,
                max_tokens=4000  # Increased to allow long descriptions
            )
            return response.choices[0].message.content or "{}"
        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            return "{}"

    # ─────────────────────────────────────────────────────────────
    # PROMPT BUILDING
    # ─────────────────────────────────────────────────────────────

    def _build_analysis_prompt(self, parsed_log: ParsedLog, ml_prediction: Dict,
                               rag_context: str, repo_context: Optional[Dict]) -> str:
        """Builds a rich user prompt with all available context."""
        error_details = []
        for i, error in enumerate(parsed_log.errors[:5], 1):
            error_details.append(f"{i}. [{error['type'].upper()}] Line {error['line_number']}: {error['message'][:300]}")

        error_block = "\n".join(error_details) if error_details else "No structured errors extracted."

        prompt = f"""## Service / Job Context
- Platform: {parsed_log.platform.value}
- Job Name: {parsed_log.job_name}
- Status: {parsed_log.status}
- Timestamp: Analysis initiated at runtime

## ML Classification
- Primary Error Type: {ml_prediction['primary_category']}
- Confidence: {ml_prediction['confidence']}

## Detected Errors ({len(parsed_log.errors)} total, top 5 shown):
{error_block}

## Relevant Knowledge Base Context
{rag_context if rag_context else "No relevant KB documents found."}
"""
        if repo_context:
            prompt += f"""
## Repository Context
{json.dumps(repo_context, indent=2)}
"""
        prompt += """
## Task
Perform the root cause analysis NOW. Remember:
- The "description" MUST be at least 250 words of deep technical detail.
- Include exact component names, exit codes, failure chains, and cascading effects.
- Provide 4–8 ordered fixes with CLI commands.
- Prevention must mention specific tools and CI/CD practices.
- Return ONLY the JSON object. No markdown fences, no extra text.
"""
        return prompt

    # ─────────────────────────────────────────────────────────────
    # POST-PROCESSING & RICHNESS ENFORCEMENT
    # ─────────────────────────────────────────────────────────────

    def _enforce_richness(self, parsed: Dict, parsed_log: ParsedLog,
                          ml_prediction: Dict, rag_context: str) -> Dict:
        """If LLM output is still short, overlay rich heuristic detail."""
        desc = parsed.get("description", "")
        fixes = parsed.get("suggested_fixes", [])

        # If description is rich and fixes are plenty, accept it
        if len(desc.split()) >= 150 and len(fixes) >= 3:
            return parsed

        logger.info("[Analyzer] Enriching terse LLM output with heuristic analysis...")
        heuristic = self._build_rich_heuristic(parsed_log, ml_prediction, rag_context)

        # Merge category/confidence/severity
        parsed["category"] = parsed.get("category") or heuristic["category"]
        parsed["confidence"] = parsed.get("confidence") or heuristic["confidence"]
        parsed["severity"] = parsed.get("severity") or heuristic["severity"]

        # Merge description
        if len(desc.split()) < 150:
            rich_desc = heuristic["description"]
            if desc and desc not in rich_desc and desc != "Analysis failed":
                parsed["description"] = f"{desc}\n\n---\n\n{rich_desc}"
            else:
                parsed["description"] = rich_desc

        # Merge fixes
        existing_fixes = [f for f in fixes if f and f.get("description")]
        heuristic_fixes = heuristic.get("suggested_fixes", [])
        # Deduplicate by description text
        seen = {f["description"] for f in existing_fixes}
        merged = existing_fixes[:]
        for h in heuristic_fixes:
            if h["description"] not in seen:
                merged.append(h)
                seen.add(h["description"])
        parsed["suggested_fixes"] = merged[:8]

        # Prevention
        if not parsed.get("prevention") or len(parsed["prevention"].split()) < 10:
            parsed["prevention"] = heuristic.get("prevention", parsed.get("prevention", ""))

        # Affected components
        if not parsed.get("affected_components"):
            parsed["affected_components"] = heuristic.get("affected_components", [])

        # Evidence
        if not parsed.get("evidence"):
            parsed["evidence"] = heuristic.get("evidence", [e["message"] for e in parsed_log.errors[:3]])

        # Analysis steps
        parsed["analysis_steps"] = parsed.get("analysis_steps") or [
            {"step": "Log Parsing", "status": "Success", "detail": "Extracted error signatures and timestamps from provided logs."},
            {"step": "Error Classification", "status": "Success", "detail": f"Classified as {parsed.get('category', 'UNKNOWN')} with confidence {parsed.get('confidence', 0)}."},
            {"step": "Root Cause Analysis", "status": "Success", "detail": "Identified primary failure component and cascading impact."},
            {"step": "Fix Generation", "status": "Success" if parsed.get("suggested_fixes") else "Skipped", "detail": f"Generated {len(parsed.get('suggested_fixes', []))} remediation steps."}
        ]

        return parsed

    def _dict_to_root_cause(self, data: Dict, parsed_log: ParsedLog) -> RootCause:
        """Convert enriched dict to RootCause dataclass."""
        category_str = data.get("category", "unknown")
        try:
            category = RootCauseCategory(category_str)
        except ValueError:
            category = RootCauseCategory.UNKNOWN

        return RootCause(
            category=category,
            description=data.get("description", "Analysis failed"),
            confidence=float(data.get("confidence", 0.5)),
            affected_components=data.get("affected_components", []),
            evidence=data.get("evidence", [e["message"] for e in parsed_log.errors[:3]]),
            suggested_fixes=data.get("suggested_fixes", []),
            references=data.get("references", []),
            severity=data.get("severity", "medium")
        )

    # ─────────────────────────────────────────────────────────────
    # RICH HEURISTIC FALLBACK (No more one-liners!)
    # ─────────────────────────────────────────────────────────────

    def _heuristic_analysis(self, parsed_log: ParsedLog, ml_prediction: Dict,
                            rag_context: str) -> RootCause:
        """Public heuristic entrypoint — returns rich detail."""
        data = self._build_rich_heuristic(parsed_log, ml_prediction, rag_context)
        return self._dict_to_root_cause(data, parsed_log)

    def _build_rich_heuristic(self, parsed_log: ParsedLog, ml_prediction: Dict,
                              rag_context: str) -> Dict:
        """Builds a deeply detailed heuristic analysis based on error signatures."""
        msg_lower = (parsed_log.raw_log + " " + " ".join(e["message"] for e in parsed_log.errors)).lower()
        error_types = {}
        for error in parsed_log.errors:
            etype = error['type']
            error_types[etype] = error_types.get(etype, 0) + 1

        # ── CrashLoopBackOff / Container failures ──
        if "crashloopbackoff" in msg_lower or "back-off restarting" in msg_lower:
            return {
                "category": "infrastructure_failure",
                "confidence": ml_prediction.get('confidence', 0.92),
                "severity": "critical",
                "description": (
                    "The pod is in a CrashLoopBackOff state, which is Kubernetes' exponential backoff mechanism "
                    "when a container fails to start repeatedly. The kubelet on the worker node detects that the "
                    "container's main process exits with a non-zero status (or crashes) immediately after startup. "
                    "It then attempts to restart the container, but because the failure is deterministic — the same "
                    "error occurs every time — Kubernetes applies an exponential backoff delay between restart attempts. "
                    "This delay grows from 10 seconds up to 5 minutes, making the pod appear 'stuck' in CrashLoopBackOff.\n\n"
                    "Common root causes include: (1) a missing or incorrect container image tag, causing the entrypoint "
                    "to fail; (2) a missing dependency or environment variable that the application requires at boot; "
                    "(3) insufficient resource limits (CPU/memory) causing the OOMKiller to terminate the process; "
                    "(4) a misconfigured liveness probe that kills the container before it finishes initialization; "
                    "(5) permission errors when trying to write to a read-only filesystem; and (6) application-level "
                    "panics due to unhandled exceptions during startup.\n\n"
                    "To diagnose, inspect the previous container's logs using `kubectl logs <pod> --previous`, "
                    "check pod events with `kubectl describe pod <pod>`, and verify resource quotas and image digests. "
                    "The exit code is critical: code 1 indicates an application error, code 137 indicates SIGKILL (often OOM), "
                    "and code 143 indicates SIGTERM. Also check init container status, as a failing init container blocks "
                    "the main container from starting entirely."
                ),
                "affected_components": list(error_types.keys()) or ["kubernetes", "container"],
                "evidence": [e["message"] for e in parsed_log.errors[:3]],
                "suggested_fixes": [
                    {"description": "Inspect previous container logs: `kubectl logs <pod-name> --previous -n <namespace>`", "priority": "critical", "automation_possible": False},
                    {"description": "Describe the pod for events: `kubectl describe pod <pod-name> -n <namespace>`", "priority": "critical", "automation_possible": False},
                    {"description": "Check resource limits in Deployment spec; increase memory/CPU if near limits.", "priority": "high", "automation_possible": True},
                    {"description": "Verify all required environment variables and ConfigMaps are mounted correctly.", "priority": "high", "automation_possible": True},
                    {"description": "Validate the container image tag exists and the entrypoint command is correct.", "priority": "high", "automation_possible": False},
                    {"description": "Review liveness/readiness probe timings — increase `initialDelaySeconds` if the app starts slowly.", "priority": "medium", "automation_possible": True},
                    {"description": "Check for OOMKilled status: `kubectl get pod <pod> -o jsonpath='{.status.containerStatuses[0].lastState.terminated.exitCode}'`", "priority": "high", "automation_possible": False},
                    {"description": "If using init containers, ensure they complete successfully before the main container starts.", "priority": "medium", "automation_possible": False}
                ],
                "prevention": (
                    "Implement container health checks in your CI/CD pipeline before deployment. Use tools like Trivy or Snyk "
                    "to scan images for missing dependencies. Set resource requests equal to realistic usage and limits with "
                    "a 20% headroom. Configure Prometheus alerts for `kube_pod_container_status_restarts_total` to detect "
                    "CrashLoopBackOff within 2 minutes. Use Helm pre-install hooks to validate configs. Enforce pod security "
                    "standards to prevent read-only filesystem violations."
                )
            }

        # ── ImagePullBackOff ──
        if "imagepullbackoff" in msg_lower or "errimagepull" in msg_lower:
            return {
                "category": "infrastructure_failure",
                "confidence": ml_prediction.get('confidence', 0.95),
                "severity": "high",
                "description": (
                    "The kubelet cannot pull the specified container image from the registry. This occurs when the image "
                    "name/tag is incorrect, the image does not exist, the registry is unreachable, or the imagePullSecrets "
                    "are missing or invalid. The kubelet schedules the pod onto a node, then the container runtime "
                    "(containerd or CRI-O) attempts to resolve and pull the image. If authentication fails or the manifest "
                    "is not found, the runtime returns an error and Kubernetes marks the container state as Waiting with reason "
                    "ImagePullBackOff. The backoff delay increases with each failed attempt. In private registries such as "
                    "ECR, GCR, ACR, or Harbor, this almost always indicates expired credentials or missing `imagePullSecrets`."
                ),
                "affected_components": list(error_types.keys()) or ["kubernetes", "registry"],
                "evidence": [e["message"] for e in parsed_log.errors[:3]],
                "suggested_fixes": [
                    {"description": "Verify image name and tag: `docker pull <image>:<tag>` from a bastion host.", "priority": "critical", "automation_possible": False},
                    {"description": "Check registry credentials: `kubectl get secret <regcred> -o json | jq -r '.data.\.dockerconfigjson' | base64 -d`", "priority": "critical", "automation_possible": False},
                    {"description": "For ECR, ensure the node IAM role has `ecr:BatchGetImage` and `ecr:GetAuthorizationToken`.", "priority": "high", "automation_possible": True},
                    {"description": "Check network connectivity from node to registry: `crictl pull <image>` or `ctr images pull`.", "priority": "high", "automation_possible": False},
                    {"description": "If using a private registry behind a firewall, verify DNS resolution and proxy settings on the node.", "priority": "medium", "automation_possible": False},
                    {"description": "Confirm the image architecture matches the node architecture (amd64 vs arm64).", "priority": "medium", "automation_possible": False}
                ],
                "prevention": (
                    "Use immutable image digests (SHA256) instead of floating tags in production. Store registry credentials "
                    "in a sealed-secret or external secret operator. Set up registry replication or a pull-through cache "
                    "(Dragonfly, Harbor proxy cache) to reduce external dependencies. Monitor `kubelet_image_pull_duration_seconds` in Prometheus."
                )
            }

        # ── OOMKilled / Memory ──
        if "oomkilled" in msg_lower or "out of memory" in msg_lower or "exit code 137" in msg_lower:
            return {
                "category": "resource_constraint",
                "confidence": ml_prediction.get('confidence', 0.90),
                "severity": "high",
                "description": (
                    "The Linux OOM Killer terminated the container process because the cgroup's memory limit was exceeded. "
                    "In Kubernetes, when a container surpasses its `resources.limits.memory`, the kernel invokes "
                    "`oom_kill_process()` which sends SIGKILL (signal 9, exit code 137). The application did not have a chance "
                    "to gracefully shut down. This is common with Java applications where the JVM heap is set too close to the "
                    "container limit, leaving no room for off-heap memory (metaspace, thread stacks, native memory). It can also "
                    "occur during memory leaks, unbounded cache growth, or sudden traffic spikes that increase concurrent request "
                    "memory footprint."
                ),
                "affected_components": list(error_types.keys()) or ["kubernetes", "container"],
                "evidence": [e["message"] for e in parsed_log.errors[:3]],
                "suggested_fixes": [
                    {"description": "Increase memory limit in Deployment: `resources.limits.memory` (ensure JVM heap is ~75% of limit).", "priority": "critical", "automation_possible": True},
                    {"description": "Set JVM flags: `-XX:+UseContainerSupport -XX:MaxRAMPercentage=75.0`.", "priority": "high", "automation_possible": True},
                    {"description": "Analyze heap dump with Eclipse MAT or JProfiler to find memory leaks.", "priority": "high", "automation_possible": False},
                    {"description": "Add Vertical Pod Autoscaler (VPA) in recommendation mode to suggest right-sized limits.", "priority": "medium", "automation_possible": True},
                    {"description": "Review application caches and connection pools — reduce max sizes if unbounded.", "priority": "medium", "automation_possible": True},
                    {"description": "Enable memory overcommit alerts: `container_memory_working_set_bytes / container_spec_memory_limit_bytes > 0.9`", "priority": "high", "automation_possible": True}
                ],
                "prevention": (
                    "Size containers based on load-test memory profiles, not guesswork. Use VPA or Goldilocks to recommend "
                    "requests and limits. Implement circuit breakers and rate limiting to prevent traffic spikes from causing "
                    "memory exhaustion. Schedule memory leak detection in CI using JMeter plus heap dump analysis."
                )
            }

        # ── Database / Connection errors ──
        if any(k in msg_lower for k in ["connection refused", "too many connections", "sqlstate", "deadlock", "timeout", "psql", "mysql"]):
            return {
                "category": "external_dependency",
                "confidence": ml_prediction.get('confidence', 0.85),
                "severity": "high",
                "description": (
                    "The application cannot establish or maintain a connection to the database. If the error is 'connection refused', "
                    "the target DB host/port is unreachable or the DB process is not listening. If it is 'too many connections', "
                    "the connection pool (HikariCP, pgBouncer, etc.) has exhausted the DB's `max_connections` limit. Deadlocks occur "
                    "when two transactions hold locks on resources the other needs, creating a circular wait. Connection timeouts "
                    "suggest network latency, firewall rules, or the DB being overloaded and unable to accept new connections within "
                    "the `connect_timeout` window."
                ),
                "affected_components": list(error_types.keys()) or ["database", "connection-pool"],
                "evidence": [e["message"] for e in parsed_log.errors[:3]],
                "suggested_fixes": [
                    {"description": "Check DB pod/node health: `kubectl get pods -l app=postgres` or check RDS CloudWatch metrics.", "priority": "critical", "automation_possible": False},
                    {"description": "Verify connection string: host, port, database name, and SSL mode.", "priority": "critical", "automation_possible": True},
                    {"description": "Scale connection pool: reduce `maximumPoolSize` in app or increase `max_connections` in PostgreSQL.", "priority": "high", "automation_possible": True},
                    {"description": "Use pgBouncer or RDS Proxy for connection multiplexing.", "priority": "high", "automation_possible": True},
                    {"description": "Kill idle connections: `SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE state = 'idle' AND state_change < NOW() - INTERVAL '10 min';`", "priority": "medium", "automation_possible": True},
                    {"description": "Analyze deadlock logs and reorder table access in transactions to consistent ordering.", "priority": "medium", "automation_possible": False},
                    {"description": "Enable query logging to identify slow queries causing queue buildup.", "priority": "medium", "automation_possible": True}
                ],
                "prevention": (
                    "Use connection pooling at both application (HikariCP) and infrastructure (PgBouncer) layers. Set up alerts on "
                    "`pg_stat_activity` count and `database_connections` metrics. Implement query timeouts and statement timeouts. "
                    "Use read replicas to distribute read load. Review ORM N+1 query patterns in code reviews."
                )
            }

        # ── Network / DNS ──
        if any(k in msg_lower for k in ["no such host", "dial tcp", "i/o timeout", "connection reset", "dns", "nxdomain"]):
            return {
                "category": "network_issue",
                "confidence": ml_prediction.get('confidence', 0.80),
                "severity": "medium",
                "description": (
                    "A network-layer failure is preventing the service from reaching its dependency. DNS resolution failures "
                    "('no such host') indicate CoreDNS misconfiguration, missing Service entries, or external DNS propagation issues. "
                    "TCP dial timeouts suggest the target service is not listening on the port, a NetworkPolicy is blocking egress, "
                    "or a firewall/SecurityGroup rule is too restrictive. Connection resets can be caused by intermediate load balancers "
                    "(NGINX, AWS ALB) timing out idle connections, or by the upstream closing sockets prematurely."
                ),
                "affected_components": list(error_types.keys()) or ["network", "dns", "service-mesh"],
                "evidence": [e["message"] for e in parsed_log.errors[:3]],
                "suggested_fixes": [
                    {"description": "Test DNS from inside the pod: `nslookup <target>` or `dig <target>`.", "priority": "high", "automation_possible": False},
                    {"description": "Check Kubernetes Service exists and selectors match pod labels.", "priority": "high", "automation_possible": True},
                    {"description": "Verify NetworkPolicies allow egress from source namespace to target namespace on the required port.", "priority": "high", "automation_possible": True},
                    {"description": "Test raw TCP: `nc -zv <target> <port>` from a debug sidecar.", "priority": "high", "automation_possible": False},
                    {"description": "Review load balancer idle timeout settings; increase if longer than application keepalive.", "priority": "medium", "automation_possible": True},
                    {"description": "Check iptables/nftables rules on the node for dropped packets.", "priority": "medium", "automation_possible": False},
                    {"description": "If cross-AZ, verify VPC routing tables and NAT Gateway health.", "priority": "medium", "automation_possible": False}
                ],
                "prevention": (
                    "Implement service mesh (Istio/Linkerd) for mTLS and observability. Use headless services for direct pod-to-pod "
                    "communication when needed. Configure CoreDNS caching and readiness probes. Add network connectivity checks "
                    "in CI using `kubectl debug` ephemeral containers."
                )
            }

        # ── Terraform / IaC errors ──
        if "terraform" in msg_lower or "invalid" in msg_lower and any(k in msg_lower for k in ["provider", "resource", "module"]):
            return {
                "category": "configuration_error",
                "confidence": ml_prediction.get('confidence', 0.88),
                "severity": "high",
                "description": (
                    "Terraform infrastructure provisioning has failed. This typically occurs due to a mismatch between the desired "
                    "state declared in HCL and the actual state in the cloud provider. Common causes include: invalid provider credentials "
                    "or expired IAM tokens; resource naming conflicts where a resource already exists; invalid attribute values that "
                    "violate provider API constraints; missing required variables or incorrect variable types; state file corruption or "
                    "lock contention when multiple pipelines run concurrently; and provider version incompatibilities where a newer "
                    "provider schema breaks existing resource definitions."
                ),
                "affected_components": list(error_types.keys()) or ["terraform", "iac", "cloud-provider"],
                "evidence": [e["message"] for e in parsed_log.errors[:3]],
                "suggested_fixes": [
                    {"description": "Run `terraform validate` and `terraform plan` locally to reproduce the error.", "priority": "critical", "automation_possible": False},
                    {"description": "Check provider credentials and IAM permissions for the target cloud account.", "priority": "critical", "automation_possible": False},
                    {"description": "Verify state file integrity: `terraform state list` and check for lock files in S3/DynamoDB.", "priority": "high", "automation_possible": False},
                    {"description": "Pin provider versions in `required_providers` to avoid breaking schema changes.", "priority": "high", "automation_possible": True},
                    {"description": "Use `terraform import` for existing resources instead of attempting to recreate them.", "priority": "medium", "automation_possible": False},
                    {"description": "Enable Terraform Cloud remote state locking to prevent concurrent execution conflicts.", "priority": "medium", "automation_possible": True}
                ],
                "prevention": (
                    "Run `terraform validate` and `terraform plan` in CI before every apply. Use Sentinel policies or OPA to enforce "
                    "naming conventions and resource tagging. Store state remotely with locking enabled. Version-pin all providers and "
                    "modules. Use atlantis or Terraform Cloud for collaborative IaC workflows with plan review gates."
                )
            }

        # ── YAML / Config syntax errors ──
        if "yaml" in msg_lower or "syntax" in msg_lower or "mapping values" in msg_lower or "did not find expected" in msg_lower:
            return {
                "category": "configuration_error",
                "confidence": ml_prediction.get('confidence', 0.90),
                "severity": "medium",
                "description": (
                    "A YAML syntax or structural error was detected in the configuration file. YAML is whitespace-sensitive, and "
                    "common mistakes include using tabs instead of spaces, incorrect indentation of nested keys, missing colons after "
                    "key names, unquoted strings that are interpreted as other types (e.g., 'yes'/'no' as booleans), and duplicate keys "
                    "in mappings. In Kubernetes manifests, this often manifests as invalid Deployment, Service, or ConfigMap specs that "
                    "fail server-side validation when applied via `kubectl apply`."
                ),
                "affected_components": list(error_types.keys()) or ["yaml", "kubernetes-manifest"],
                "evidence": [e["message"] for e in parsed_log.errors[:3]],
                "suggested_fixes": [
                    {"description": "Validate YAML syntax: `yamllint <file>` or use an online parser.", "priority": "high", "automation_possible": True},
                    {"description": "Convert tabs to spaces (YAML requires 2 or 4 spaces per indentation level).", "priority": "high", "automation_possible": True},
                    {"description": "Validate Kubernetes manifests: `kubectl apply --dry-run=client -f <file>`", "priority": "high", "automation_possible": True},
                    {"description": "Use `helm lint` if the manifest is part of a Helm chart.", "priority": "medium", "automation_possible": True},
                    {"description": "Quote ambiguous strings like version numbers and booleans explicitly.", "priority": "medium", "automation_possible": True}
                ],
                "prevention": (
                    "Integrate `yamllint` and `kubeval` or `kubeconform` into pre-commit hooks and CI pipelines. Use Helm schema validation "
                    "(`values.schema.json`) to catch type mismatches early. Enforce editorconfig rules for consistent indentation across teams."
                )
            }

        # ── Docker / Build errors ──
        if "docker" in error_types or "dockerfile" in msg_lower or "build" in msg_lower and "stage" in msg_lower:
            return {
                "category": "dependency_issue",
                "confidence": ml_prediction.get('confidence', 0.85),
                "severity": "high",
                "description": (
                    "A Docker build or runtime failure was detected. Build failures typically stem from invalid Dockerfile syntax, "
                    "missing base images, failed package installations (apt, yum, pip, npm), or multi-stage build COPY instructions "
                    "referencing non-existent build artifacts. Runtime failures include missing shared libraries, incorrect ENTRYPOINT/CMD "
                    "definitions, permission denied on exposed ports below 1024 when running as non-root, and health check failures "
                    "due to missing curl/wget in minimal images (distroless, scratch)."
                ),
                "affected_components": list(error_types.keys()) or ["docker", "container"],
                "evidence": [e["message"] for e in parsed_log.errors[:3]],
                "suggested_fixes": [
                    {"description": "Build locally to reproduce: `docker build -t test:latest .` and inspect layer cache.", "priority": "critical", "automation_possible": False},
                    {"description": "Check base image availability and architecture compatibility.", "priority": "high", "automation_possible": False},
                    {"description": "Verify all COPY/ADD source paths exist in the build context.", "priority": "high", "automation_possible": True},
                    {"description": "For multi-stage builds, ensure artifacts are built in the correct stage before COPY.", "priority": "high", "automation_possible": True},
                    {"description": "Add required tools to minimal images or use debug sidecars for health checks.", "priority": "medium", "automation_possible": True}
                ],
                "prevention": (
                    "Use BuildKit for faster, more reliable builds with better caching. Pin base image digests instead of tags. "
                    "Run `docker build` in CI with `--no-cache` periodically to catch stale dependency issues. Use Hadolint for Dockerfile linting."
                )
            }

        # ── Generic / Default rich fallback ──
        return {
            "category": "unknown",
            "confidence": ml_prediction.get('confidence', 0.50),
            "severity": "medium",
            "description": (
                f"An error was detected in the deployment logs for job '{parsed_log.job_name}'. The ML classifier identified "
                f"the primary error type as '{ml_prediction.get('primary_category', 'unknown')}' with confidence "
                f"{ml_prediction.get('confidence', 0)}. Without a more specific error signature, a broad diagnostic approach is required. "
                "First, correlate the error timestamp with deployment events, infrastructure changes, and traffic patterns to identify "
                "a trigger. Second, examine the full stack trace and surrounding log lines for nested exceptions or causal chains. "
                "Third, check resource utilization (CPU, memory, disk I/O, network) on the affected node or pod to rule out resource "
                "contention. Fourth, verify upstream and downstream dependency health — often the root cause is not the service logging "
                "the error but a dependency failing silently or timing out. Fifth, review recent configuration changes (ConfigMaps, "
                "Secrets, feature flags) that could alter application behavior."
            ),
            "affected_components": list(error_types.keys()) or ["unknown"],
            "evidence": [e["message"] for e in parsed_log.errors[:3]],
            "suggested_fixes": [
                {"description": "Collect and centralize all logs from the affected service and its dependencies.", "priority": "high", "automation_possible": True},
                {"description": "Check infrastructure dashboards (Grafana, Datadog, CloudWatch) for anomalies at the error timestamp.", "priority": "high", "automation_possible": False},
                {"description": "Roll back the most recent deployment to determine if the error is code-related.", "priority": "high", "automation_possible": True},
                {"description": "Run the application locally with the same data/configuration to reproduce the issue.", "priority": "medium", "automation_possible": False},
                {"description": "Enable verbose/debug logging temporarily to capture more diagnostic detail.", "priority": "medium", "automation_possible": True},
                {"description": "Review dependency changelogs for breaking changes or known bugs in current versions.", "priority": "low", "automation_possible": False}
            ],
            "prevention": (
                "Establish a blameless postmortem culture. Every incident should produce runbook updates and automated test cases. "
                "Use feature flags to dark-launch risky changes. Implement chaos engineering (Chaos Monkey, Litmus) to proactively "
                "discover failure modes. Maintain golden signals (latency, traffic, errors, saturation) dashboards for every service."
            )
        }

    # ─────────────────────────────────────────────────────────────
    # UTILITIES
    # ─────────────────────────────────────────────────────────────

    @staticmethod
    def _safe_parse_json(text: str) -> Dict:
        """Robustly extract JSON from LLM response (handles markdown fences)."""
        if not text or not text.strip():
            return {}
        text = text.strip()
        if text.startswith("```"):
            text = re.sub(r"^```(?:json)?\s*", "", text)
            text = re.sub(r"\s*```$", "", text)
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", text, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(0))
                except json.JSONDecodeError:
                    pass
            logger.warning("[Analyzer] JSON parse failed, returning raw text in description field")
            return {"description": text}

    # ─────────────────────────────────────────────────────────────
    # FIX STRATEGY (unchanged logic, kept for compatibility)
    # ─────────────────────────────────────────────────────────────

    def generate_fix_strategy(self, root_cause: RootCause, file_context: Dict) -> Dict:
        strategy = {
            "root_cause": {
                "category": root_cause.category.value,
                "description": root_cause.description,
                "confidence": root_cause.confidence,
                "severity": root_cause.severity
            },
            "files_to_modify": [], "commands_to_run": [],
            "verification_steps": [], "risk_assessment": "low", "rollback_plan": ""
        }
        if root_cause.category == RootCauseCategory.CONFIGURATION_ERROR:
            if "docker" in root_cause.affected_components:
                strategy["files_to_modify"].extend(["Dockerfile", ".dockerignore", "docker-compose.yml"])
            if "kubernetes" in root_cause.affected_components:
                strategy["files_to_modify"].extend(["*.yaml", "*.yml", "k8s/", "helm/"])
            if "terraform" in root_cause.affected_components:
                strategy["files_to_modify"].extend(["*.tf", "*.tfvars"])
        elif root_cause.category == RootCauseCategory.RESOURCE_CONSTRAINT:
            strategy["files_to_modify"].extend(["deployment.yaml", "values.yaml", "terraform/"])
            strategy["commands_to_run"].extend(["kubectl top nodes", "kubectl describe resourcequota"])
        elif root_cause.category == RootCauseCategory.PERMISSION_ISSUE:
            strategy["files_to_modify"].extend(["rbac.yaml", "serviceaccount.yaml", "*.tf"])
            strategy["commands_to_run"].append("kubectl auth can-i --list")
        strategy["verification_steps"] = [
            "Run local validation tests", "Deploy to staging environment",
            "Monitor metrics for 30 minutes", "Verify all health checks pass"
        ]
        if root_cause.severity == "critical":
            strategy["risk_assessment"] = "high"
            strategy["rollback_plan"] = "Immediate rollback to previous stable version"
        elif root_cause.severity == "high":
            strategy["risk_assessment"] = "medium"
            strategy["rollback_plan"] = "Revert PR and redeploy previous version"
        return strategy