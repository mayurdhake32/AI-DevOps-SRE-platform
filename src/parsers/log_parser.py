"""
Universal CI/CD Log Parser
Supports GitHub Actions, Jenkins, GitLab CI, CircleCI, Azure DevOps
"""
import re
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
from datetime import datetime


class CIPlatform(Enum):
    GITHUB_ACTIONS = "github_actions"
    JENKINS = "jenkins"
    GITLAB_CI = "gitlab_ci"
    CIRCLECI = "circleci"
    AZURE_DEVOPS = "azure_devops"
    UNKNOWN = "unknown"


@dataclass
class ParsedLog:
    platform: CIPlatform
    job_name: str
    status: str
    stages: List[Dict[str, Any]]
    errors: List[Dict[str, Any]]
    warnings: List[Dict[str, Any]]
    duration_seconds: Optional[float]
    raw_log: str
    metadata: Dict[str, Any]


class LogParser:
    """
    Universal log parser that auto-detects CI platform and extracts structured data.
    """
    
    DOCKER_ERROR_PATTERNS = [
        r"(?i)docker.*error",
        r"(?i)failed to build",
        r"(?i)no such image",
        r"(?i)pull access denied",
        r"(?i)container .* exited with code [1-9]",
        r"(?i)docker daemon.*error",
        r"(?i)cannot connect to docker daemon",
    ]
    
    K8S_ERROR_PATTERNS = [
        r"(?i)pod.*(failed|error|crashloopbackoff)",
        r"(?i)deployment.*(failed|unavailable)",
        r"(?i)service.*(not found|timeout)",
        r"(?i)configmap.*(not found|error)",
        r"(?i)secret.*(not found|error)",
        r"(?i)ingress.*(error|failed)",
        r"(?i)node.*(not ready|unschedulable)",
        r"(?i)persistentvolume.*(failed|bound)",
        r"(?i)helm.*(failed|error)",
        r"(?i)kubectl.*(error|failed)",
    ]
    
    TERRAFORM_ERROR_PATTERNS = [
        r"(?i)terraform.*error",
        r"(?i)failed to\s+\w+",
        r"(?i)invalid\s+\w+",
        r"(?i)resource\s+\w+\s+not found",
        r"(?i)provider\s+\w+\s+error",
        r"(?i)state\s+lock\s+error",
        r"(?i)authorization\s+failed",
        r"(?i)timeout\s+while\s+\w+",
    ]
    
    YAML_ERROR_PATTERNS = [
        r"(?i)yaml.*error",
        r"(?i)mapping values are not allowed",
        r"(?i)did not find expected key",
        r"(?i)invalid\s+\w+\s+in\s+yaml",
    ]
    
    def __init__(self):
        self.error_patterns = {
            "docker": [re.compile(p) for p in self.DOCKER_ERROR_PATTERNS],
            "kubernetes": [re.compile(p) for p in self.K8S_ERROR_PATTERNS],
            "terraform": [re.compile(p) for p in self.TERRAFORM_ERROR_PATTERNS],
            "yaml": [re.compile(p) for p in self.YAML_ERROR_PATTERNS],
        }
    
    def detect_platform(self, log_content: str) -> CIPlatform:
        """Auto-detect CI/CD platform from log content."""
        indicators = {
            CIPlatform.GITHUB_ACTIONS: ["::error::", "::warning::", "::group::", "github_actions"],
            CIPlatform.JENKINS: ["[Pipeline]", "Started by user", "Building in workspace", "Finished: "],
            CIPlatform.GITLAB_CI: ["Running with gitlab-runner", "section_start:", "section_end:"],
            CIPlatform.CIRCLECI: ["CircleCI received exit code", "#!/bin/sh -eo pipefail"],
            CIPlatform.AZURE_DEVOPS: ["##vso[", "Azure Pipelines", "Agent.JobName"],
        }
        
        for platform, markers in indicators.items():
            if any(marker in log_content for marker in markers):
                return platform
        return CIPlatform.UNKNOWN
    
    def parse(self, log_content: str, platform: Optional[CIPlatform] = None) -> ParsedLog:
        """Parse raw CI/CD log into structured format."""
        if platform is None:
            platform = self.detect_platform(log_content)
        
        lines = log_content.split("\n")
        
        # Extract job name
        job_name = self._extract_job_name(lines, platform)
        
        # Extract status
        status = self._extract_status(lines, platform)
        
        # Extract stages/phases
        stages = self._extract_stages(lines, platform)
        
        # Extract errors with context
        errors = self._extract_errors(lines)
        
        # Extract warnings
        warnings = self._extract_warnings(lines, platform)
        
        # Calculate duration
        duration = self._extract_duration(lines, platform)
        
        return ParsedLog(
            platform=platform,
            job_name=job_name,
            status=status,
            stages=stages,
            errors=errors,
            warnings=warnings,
            duration_seconds=duration,
            raw_log=log_content,
            metadata={"parsed_at": datetime.utcnow().isoformat()}
        )
    
    def _extract_job_name(self, lines: List[str], platform: CIPlatform) -> str:
        patterns = {
            CIPlatform.GITHUB_ACTIONS: r"Run .*?/(.*?)(?:\n|\r|$)",
            CIPlatform.JENKINS: r"Building (.*?) #",
            CIPlatform.GITLAB_CI: r"job=(.*?)(?:\s|$)",
        }
        pattern = patterns.get(platform, r"Job: (.*)")
        for line in lines[:20]:
            match = re.search(pattern, line)
            if match:
                return match.group(1).strip()
        return "unknown-job"
    
    def _extract_status(self, lines: List[str], platform: CIPlatform) -> str:
        check_lines = lines[-50:] if len(lines) > 50 else lines
        for line in reversed(check_lines):
            if platform == CIPlatform.GITHUB_ACTIONS and "exit code" in line.lower():
                return "failure" if any(x in line for x in ["exit code 1", "exit code 2"]) else "success"
            elif platform == CIPlatform.JENKINS and "Finished: " in line:
                if "SUCCESS" in line: 
                    return "success"
                elif "FAILURE" in line: 
                    return "failure"
                elif "UNSTABLE" in line: 
                    return "unstable"
            elif "error" in line.lower() or "failed" in line.lower():
                return "failure"
        return "unknown"
    
    def _extract_stages(self, lines: List[str], platform: CIPlatform) -> List[Dict]:
        stages = []
        current_stage = None
        
        for line in lines:
            if "::group::" in line:
                current_stage = {"name": line.split("::group::")[1], "start_line": len(stages), "logs": []}
            elif "::endgroup::" in line and current_stage:
                stages.append(current_stage)
                current_stage = None
            elif "[Pipeline] {" in line or "[Pipeline] stage" in line:
                stage_name = re.search(r"stage\s*\((.*?)\)", line)
                current_stage = {"name": stage_name.group(1) if stage_name else "unknown", "logs": []}
            elif "[Pipeline] }" in line and current_stage:
                stages.append(current_stage)
                current_stage = None
            
            if current_stage:
                current_stage["logs"].append(line)
        
        return stages
    
    def _extract_errors(self, lines: List[str]) -> List[Dict]:
        errors = []
        for i, line in enumerate(lines):
            for error_type, patterns in self.error_patterns.items():
                for pattern in patterns:
                    if pattern.search(line):
                        start = max(0, i - 5)
                        end = min(len(lines), i + 6)
                        context = "\n".join(lines[start:end])
                        
                        errors.append({
                            "type": error_type,
                            "line_number": i + 1,
                            "message": line.strip(),
                            "context": context,
                            "severity": "critical" if error_type in ["docker", "kubernetes"] else "high"
                        })
                        break
        return errors
    
    def _extract_warnings(self, lines: List[str], platform: CIPlatform) -> List[Dict]:
        warnings = []
        warning_patterns = [
            r"(?i)warning:",
            r"(?i)deprecated",
            r"(?i)obsolete",
            r"(?i)will be removed",
        ]
        
        for i, line in enumerate(lines):
            for pattern in warning_patterns:
                if re.search(pattern, line):
                    warnings.append({
                        "line_number": i + 1,
                        "message": line.strip(),
                    })
                    break
        return warnings
    
    def _extract_duration(self, lines: List[str], platform: CIPlatform) -> Optional[float]:
        time_pattern = r"(\d{2}:\d{2}:\d{2})"
        times = []
        for line in lines:
            matches = re.findall(time_pattern, line)
            if matches:
                times.append(matches[0])
        
        if len(times) >= 2:
            try:
                fmt = "%H:%M:%S"
                start = datetime.strptime(times[0], fmt)
                end = datetime.strptime(times[-1], fmt)
                duration = (end - start).total_seconds()
                return duration if duration >= 0 else None
            except ValueError:
                pass
        return None
    
    def get_error_summary(self, parsed_log: ParsedLog) -> Dict[str, Any]:
        """Generate a summary of errors found in the log."""
        error_types = {}
        for error in parsed_log.errors:
            etype = error["type"]
            error_types[etype] = error_types.get(etype, 0) + 1
        
        return {
            "total_errors": len(parsed_log.errors),
            "error_types": error_types,
            "has_critical_errors": any(e["severity"] == "critical" for e in parsed_log.errors),
            "primary_error_type": max(error_types, key=error_types.get) if error_types else None,
            "platform": parsed_log.platform.value,
            "job_name": parsed_log.job_name,
            "status": parsed_log.status,
        }