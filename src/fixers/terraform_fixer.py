"""Terraform Configuration Fixer"""
import re
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from src.utils.logger import get_logger

logger = get_logger(__name__)

@dataclass
class TerraformFix:
    original: str
    fixed: str
    issue_type: str
    description: str

class TerraformFixer:
    def __init__(self):
        self.fixes_applied: List[TerraformFix] = []
    
    def fix_file(self, content: str, error_context: Optional[str] = None) -> Tuple[str, List[TerraformFix]]:
        self.fixes_applied = []
        content = self._fix_formatting(content)
        content = self._add_required_providers(content)
        content = self._fix_variable_defaults(content)
        if error_context:
            content = self._apply_error_fixes(content, error_context)
        return content, self.fixes_applied
    
    def _fix_formatting(self, content: str) -> str:
        content = re.sub(r'{\s*\n', '{\n', content)
        content = re.sub(r'\n\s*}', '\n}', content)
        return content
    
    def _add_required_providers(self, content: str) -> str:
        if 'required_providers' not in content and 'terraform {' not in content:
            block = 'terraform {\n  required_version = ">= 1.0"\n  required_providers {\n    aws = {\n      source  = "hashicorp/aws"\n      version = "~> 5.0"\n    }\n  }\n}\n\n'
            content = block + content
            self.fixes_applied.append(TerraformFix(
                original="", fixed="Added terraform block with required_providers",
                issue_type="configuration", description="Added required providers block"))
        return content
    
    def _fix_variable_defaults(self, content: str) -> str:
        lines = content.split('\n')
        new_lines = []
        i = 0
        while i < len(lines):
            new_lines.append(lines[i])
            if re.match(r'^\s*variable\s+"[^"]+"\s*{', lines[i]):
                j = i + 1
                has_default = False
                brace_count = 1
                while j < len(lines) and brace_count > 0:
                    if 'default' in lines[j]: has_default = True
                    if '{' in lines[j]: brace_count += lines[j].count('{')
                    if '}' in lines[j]: brace_count -= lines[j].count('}')
                    j += 1
                if not has_default:
                    indent = len(lines[i]) - len(lines[i].lstrip()) + 2
                    new_lines.insert(j - 1, ' ' * indent + 'default = ""')
                    self.fixes_applied.append(TerraformFix(
                        original="variable without default", fixed="Added default value",
                        issue_type="best_practice", description="Added default to variable"))
            i += 1
        return '\n'.join(new_lines)
    
    def _apply_error_fixes(self, content: str, error_context: str) -> str:
        error_lower = error_context.lower()
        if 'state lock' in error_lower:
            self.fixes_applied.append(TerraformFix(
                original="", fixed="Run: terraform force-unlock <LOCK_ID>",
                issue_type="state", description="State lock detected"))
        if 'provider configuration' in error_lower:
            content = self._add_required_providers(content)
        if 'resource already exists' in error_lower:
            self.fixes_applied.append(TerraformFix(
                original="", fixed="terraform import <resource_type>.<name> <id>",
                issue_type="import", description="Resource exists - needs import"))
        if 'authorization failed' in error_lower or 'access denied' in error_lower:
            self.fixes_applied.append(TerraformFix(
                original="", fixed="Check AWS credentials and IAM permissions",
                issue_type="permission", description="Authorization failure"))
        return content