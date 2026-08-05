"""Docker Configuration Fixer"""
import re
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from src.utils.logger import get_logger

logger = get_logger(__name__)

@dataclass
class DockerFix:
    original: str
    fixed: str
    issue_type: str
    description: str
    line_number: int

class DockerFixer:
    def __init__(self):
        self.fixes_applied: List[DockerFix] = []
    
    def fix_dockerfile(self, content: str, error_context: Optional[str] = None) -> Tuple[str, List[DockerFix]]:
        self.fixes_applied = []
        content = self._add_non_root_user(content)
        content = self._optimize_layer_caching(content)
        content = self._add_healthcheck(content)
        content = self._fix_base_image_tags(content)
        if error_context:
            content = self._apply_error_fixes(content, error_context)
        return content, self.fixes_applied
    
    def _add_non_root_user(self, content: str) -> str:
        if "USER" not in content:
            lines = content.split("\n")
            insert_idx = len(lines)
            for i, line in enumerate(lines):
                if line.strip().startswith(("CMD", "ENTRYPOINT")):
                    insert_idx = i
                    break
            user_lines = [
                "# Create non-root user",
                "RUN addgroup --system appgroup && adduser --system --group appuser",
                "USER appuser", ""
            ]
            lines = lines[:insert_idx] + user_lines + lines[insert_idx:]
            self.fixes_applied.append(DockerFix(
                original="", fixed="Added non-root user (appuser)",
                issue_type="security", description="Container runs as root - added non-root user",
                line_number=insert_idx))
            return "\n".join(lines)
        return content
    
    def _optimize_layer_caching(self, content: str) -> str:
        lines = content.split("\n")
        copy_all_idx = None
        install_idx = None
        for i, line in enumerate(lines):
            if re.match(r"^\s*COPY\s+\.\s+\.", line):
                copy_all_idx = i
            if any(cmd in line for cmd in ["npm install", "pip install", "go mod", "bundle install"]):
                install_idx = i
        if copy_all_idx is not None and install_idx is not None and copy_all_idx < install_idx:
            dep_files = self._detect_dependency_files(content)
            if dep_files:
                copy_dep = f"COPY {dep_files} ./"
                lines.insert(copy_all_idx, copy_dep)
                lines.insert(copy_all_idx + 1, lines[install_idx + 1])
                del lines[install_idx + 2]
                self.fixes_applied.append(DockerFix(
                    original="COPY . . before dependency install",
                    fixed="Copy dependency files first for better caching",
                    issue_type="optimization", description="Optimized layer caching",
                    line_number=copy_all_idx))
        return "\n".join(lines)
    
    def _detect_dependency_files(self, content: str) -> str:
        if "package.json" in content: return "package*.json"
        elif "requirements.txt" in content: return "requirements.txt"
        elif "go.mod" in content: return "go.mod go.sum"
        elif "pom.xml" in content: return "pom.xml"
        return ""
    
    def _add_healthcheck(self, content: str) -> str:
        if "HEALTHCHECK" not in content:
            lines = content.split("\n")
            insert_idx = len(lines)
            for i, line in enumerate(lines):
                if line.strip().startswith(("CMD", "ENTRYPOINT")):
                    insert_idx = i
                    break
            healthcheck = [
                "# Health check",
                "HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \\",
                "  CMD curl -f http://localhost:8080/health || exit 1", ""
            ]
            lines = lines[:insert_idx] + healthcheck + lines[insert_idx:]
            self.fixes_applied.append(DockerFix(
                original="", fixed="Added HEALTHCHECK instruction",
                issue_type="reliability", description="Added container health check",
                line_number=insert_idx))
            return "\n".join(lines)
        return content
    
    def _fix_base_image_tags(self, content: str) -> str:
        original = content
        content = re.sub(r"FROM\s+(\w+):latest", lambda m: f"FROM {m.group(1)}:alpine", content)
        if content != original:
            self.fixes_applied.append(DockerFix(
                original=":latest tag", fixed="Specific version tag",
                issue_type="reliability", description="Replaced 'latest' tag", line_number=1))
        return content
    
    def _apply_error_fixes(self, content: str, error_context: str) -> str:
        error_lower = error_context.lower()
        if "permission denied" in error_lower:
            content = self._fix_permissions(content)
        if "exited with code 137" in error_lower:
            self.fixes_applied.append(DockerFix(
                original="", fixed="Container killed (OOM)",
                issue_type="resource", description="Container ran out of memory", line_number=0))
        if "cannot find module" in error_lower:
            if "npm install" in content:
                content = content.replace("npm install", "npm ci", 1)
                self.fixes_applied.append(DockerFix(
                    original="npm install", fixed="npm ci",
                    issue_type="dependency", description="Use npm ci", line_number=0))
        return content
    
    def _fix_permissions(self, content: str) -> str:
        if "chmod" not in content:
            lines = content.split("\n")
            for i, line in enumerate(lines):
                if line.strip().startswith("COPY"):
                    lines.insert(i + 1, "RUN chmod -R 755 /app")
                    self.fixes_applied.append(DockerFix(
                        original="", fixed="Added chmod",
                        issue_type="permission", description="Fixed permissions", line_number=i+1))
                    break
            return "\n".join(lines)
        return content
    
    def generate_dockerignore(self, project_type: str = "generic") -> str:
        templates = {
            "node": "node_modules\nnpm-debug.log\nDockerfile\n.dockerignore\n.git\n.env\n.env.local\ncoverage\n.vscode\n.idea\n*.md\n.gitignore\n",
            "python": "__pycache__\n*.pyc\n*.pyo\n*.pyd\n.Python\nenv/\nvenv/\n.env\n*.egg-info/\ndist/\nbuild/\n.git\n.gitignore\nDockerfile\n.dockerignore\n.pytest_cache/\n",
            "generic": ".git\n.gitignore\nDockerfile\n.dockerignore\nREADME.md\n*.md\n.env\n.vscode\n.idea\n"
        }
        return templates.get(project_type, templates["generic"])