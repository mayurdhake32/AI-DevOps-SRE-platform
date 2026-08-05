"""
YAML Configuration Fixer
"""
import re
import yaml
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from src.utils.logger import get_logger

logger = get_logger(__name__)

@dataclass
class YAMLFix:
    original_line: str
    fixed_line: str
    line_number: int
    issue_type: str
    description: str
    confidence: float

class YAMLFixer:
    COMMON_ISSUES = {
        "indentation_error": {
            "pattern": r"^\s*\t+",
            "fix": lambda line: line.replace("\t", "  "),
            "description": "Tabs used instead of spaces"
        },
        "trailing_whitespace": {
            "pattern": r"\s+$",
            "fix": lambda line: line.rstrip(),
            "description": "Trailing whitespace"
        },
        "missing_space_after_colon": {
            "pattern": r"([\w-]+):(?! )(?!\n)",
            "fix": lambda line: re.sub(r"([\w-]+):(?! )(?!\n)", r"\1: ", line),
            "description": "Missing space after colon"
        },
    }
    
    def __init__(self, use_llm: bool = True):
        self.use_llm = use_llm
        self.fixes_applied: List[YAMLFix] = []
    
    def fix_file(self, file_path: str, error_context: Optional[str] = None) -> Tuple[str, List[YAMLFix]]:
        self.fixes_applied = []
        try:
            with open(file_path, 'r') as f:
                content = f.read()
        except Exception as e:
            logger.error(f"Failed to read {file_path}: {e}")
            return "", []
        original_content = content
        content = self._fix_syntax_errors(content)
        content = self._fix_kubernetes_issues(content, file_path)
        if error_context:
            content = self._apply_targeted_fix(content, error_context)
        is_valid, validation_error = self._validate_yaml(content)
        if not is_valid and self.use_llm:
            content = self._llm_fix(content, validation_error)
        return content, self.fixes_applied
    
    def _fix_syntax_errors(self, content: str) -> str:
        lines = content.split("\n")
        fixed_lines = []
        for i, line in enumerate(lines):
            original = line
            for issue_name, issue_config in self.COMMON_ISSUES.items():
                if re.search(issue_config["pattern"], line):
                    line = issue_config["fix"](line)
                    if line != original:
                        self.fixes_applied.append(YAMLFix(
                            original_line=original, fixed_line=line,
                            line_number=i + 1, issue_type=issue_name,
                            description=issue_config["description"], confidence=0.95
                        ))
            fixed_lines.append(line)
        return "\n".join(fixed_lines)
    
    def _fix_kubernetes_issues(self, content: str, file_path: str) -> str:
        if not any(x in file_path.lower() for x in [".yaml", ".yml", "k8s", "kube", "helm"]):
            return content
        try:
            documents = list(yaml.safe_load_all(content))
            if not documents or not any(doc for doc in documents if doc):
                return content
            fixed_docs = []
            for doc in documents:
                if not doc:
                    fixed_docs.append(doc)
                    continue
                if doc.get("kind") == "Deployment":
                    doc = self._ensure_resource_limits(doc)
                    doc = self._ensure_probes(doc)
                    doc = self._ensure_security_context(doc)
                elif doc.get("kind") == "Service":
                    doc = self._fix_service_selector(doc)
                fixed_docs.append(doc)
            fixed_content = ""
            for i, doc in enumerate(fixed_docs):
                if i > 0:
                    fixed_content += "\n---\n"
                fixed_content += yaml.dump(doc, default_flow_style=False, sort_keys=False, allow_unicode=True)
            return fixed_content
        except Exception as e:
            logger.warning(f"Kubernetes fix failed: {e}")
            return content
    
    def _ensure_resource_limits(self, doc: Dict) -> Dict:
        try:
            containers = doc.get("spec", {}).get("template", {}).get("spec", {}).get("containers", [])
            for container in containers:
                if "resources" not in container:
                    container["resources"] = {
                        "requests": {"memory": "128Mi", "cpu": "100m"},
                        "limits": {"memory": "512Mi", "cpu": "500m"}
                    }
                    self.fixes_applied.append(YAMLFix(
                        original_line="", fixed_line=f"Added resource limits for {container.get('name', 'unknown')}",
                        line_number=0, issue_type="missing_resources",
                        description="Added default resource limits", confidence=0.9
                    ))
        except Exception:
            pass
        return doc
    
    def _ensure_probes(self, doc: Dict) -> Dict:
        try:
            containers = doc.get("spec", {}).get("template", {}).get("spec", {}).get("containers", [])
            for container in containers:
                if "livenessProbe" not in container and container.get("ports"):
                    port = container["ports"][0].get("containerPort", 8080)
                    container["livenessProbe"] = {
                        "httpGet": {"path": "/health", "port": port},
                        "initialDelaySeconds": 30, "periodSeconds": 10
                    }
                    self.fixes_applied.append(YAMLFix(
                        original_line="", fixed_line=f"Added livenessProbe",
                        line_number=0, issue_type="missing_probes",
                        description="Added liveness probe", confidence=0.85
                    ))
        except Exception:
            pass
        return doc
    
    def _ensure_security_context(self, doc: Dict) -> Dict:
        try:
            pod_spec = doc.get("spec", {}).get("template", {}).get("spec", {})
            if "securityContext" not in pod_spec:
                pod_spec["securityContext"] = {
                    "runAsNonRoot": True,
                    "seccompProfile": {"type": "RuntimeDefault"}
                }
        except Exception:
            pass
        return doc
    
    def _fix_service_selector(self, doc: Dict) -> Dict:
        try:
            if doc.get("kind") == "Service":
                selector = doc.get("spec", {}).get("selector", {})
                if not selector:
                    doc["spec"]["selector"] = {"app": "default-app"}
                    self.fixes_applied.append(YAMLFix(
                        original_line="", fixed_line="Added default selector to Service",
                        line_number=0, issue_type="missing_selector",
                        description="Service missing selector", confidence=0.8
                    ))
        except Exception:
            pass
        return doc
    
    def _apply_targeted_fix(self, content: str, error_context: str) -> str:
        error_lower = error_context.lower()
        if any(x in error_lower for x in ["oomkilled", "out of memory", "memory limit"]):
            content = self._increase_memory_limits(content)
        if "imagepullbackoff" in error_lower or "pull access" in error_lower:
            content = self._fix_image_reference(content)
        if "permission denied" in error_lower or "forbidden" in error_lower:
            content = self._fix_permissions(content)
        return content
    
    def _increase_memory_limits(self, content: str) -> str:
        def replace_memory(match):
            current = match.group(1)
            if "Mi" in current:
                val = int(current.replace("Mi", "")) * 2
                return f'memory: "{val}Mi"'
            elif "Gi" in current:
                val = float(current.replace("Gi", "")) * 2
                return f'memory: "{val}Gi"'
            return match.group(0)
        return re.sub(r'memory:\s*"([^"]+)"', replace_memory, content)
    
    def _fix_image_reference(self, content: str) -> str:
        if ":latest" in content and "imagePullPolicy" not in content:
            content = content.replace("image:", "imagePullPolicy: Always\n        image:", 1)
        return content
    
    def _fix_permissions(self, content: str) -> str:
        if "securityContext" not in content:
            content = content.replace("spec:", "spec:\n      securityContext:\n        runAsUser: 1000\n        runAsGroup: 3000", 1)
        return content
    
    def _validate_yaml(self, content: str) -> Tuple[bool, Optional[str]]:
        try:
            list(yaml.safe_load_all(content))
            return True, None
        except yaml.YAMLError as e:
            return False, str(e)
    
    def _llm_fix(self, content: str, error_message: str) -> str:
        if not self.use_llm:
            return content
        try:
            import openai
            client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            prompt = f"""Fix the following YAML file. Error: {error_message}\n\nOriginal YAML:\n```yaml\n{content}\n```\n\nProvide only the fixed YAML content without any explanation."""
            response = client.chat.completions.create(
                model="gpt-4", messages=[{"role": "user", "content": prompt}],
                temperature=0.1, max_tokens=2000
            )
            fixed = response.choices[0].message.content
            if "```yaml" in fixed:
                fixed = fixed.split("```yaml")[1].split("```")[0]
            elif "```" in fixed:
                fixed = fixed.split("```")[1].split("```")[0]
            self.fixes_applied.append(YAMLFix(
                original_line="", fixed_line="LLM-based YAML correction",
                line_number=0, issue_type="llm_fix",
                description=f"Applied LLM fix for: {error_message[:100]}", confidence=0.75
            ))
            return fixed.strip()
        except Exception as e:
            logger.error(f"LLM fix failed: {e}")
            return content
    
    def generate_diff(self, original: str, fixed: str) -> str:
        import difflib
        return "\n".join(difflib.unified_diff(
            original.splitlines(), fixed.splitlines(),
            fromfile="original", tofile="fixed", lineterm=""
        ))