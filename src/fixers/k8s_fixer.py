"""Kubernetes Manifest Fixer"""
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
import yaml
import re
from src.utils.logger import get_logger

logger = get_logger(__name__)

@dataclass
class K8sFix:
    resource: str
    issue: str
    fix: str
    severity: str

class K8sFixer:
    def __init__(self):
        self.fixes_applied: List[K8sFix] = []
    
    def fix_manifest(self, content: str, error_context: Optional[str] = None) -> Tuple[str, List[K8sFix]]:
        self.fixes_applied = []
        try:
            docs = list(yaml.safe_load_all(content))
            fixed_docs = []
            for doc in docs:
                if not doc:
                    fixed_docs.append(doc)
                    continue
                kind = doc.get('kind', '')
                if kind == 'Deployment':
                    doc = self._fix_deployment(doc)
                elif kind == 'Service':
                    doc = self._fix_service(doc)
                elif kind == 'Ingress':
                    doc = self._fix_ingress(doc)
                elif kind == 'ConfigMap':
                    doc = self._fix_configmap(doc)
                fixed_docs.append(doc)
            output = ""
            for i, doc in enumerate(fixed_docs):
                if i > 0:
                    output += "\n---\n"
                output += yaml.dump(doc, default_flow_style=False, sort_keys=False, allow_unicode=True)
            if error_context:
                output = self._apply_error_specific_fixes(output, error_context)
            return output, self.fixes_applied
        except Exception as e:
            logger.error(f"K8s fix failed: {e}")
            return content, []
    
    def _fix_deployment(self, doc: Dict) -> Dict:
        spec = doc.setdefault('spec', {}).setdefault('template', {}).setdefault('spec', {})
        containers = spec.setdefault('containers', [])
        for container in containers:
            if 'resources' not in container:
                container['resources'] = {
                    'requests': {'memory': '128Mi', 'cpu': '100m'},
                    'limits': {'memory': '512Mi', 'cpu': '500m'}
                }
                self.fixes_applied.append(K8sFix(
                    resource=doc.get('metadata', {}).get('name', 'unknown'),
                    issue="Missing resource limits", fix="Added default resource limits",
                    severity="high"))
            if 'livenessProbe' not in container and container.get('ports'):
                port = container['ports'][0].get('containerPort', 8080)
                container['livenessProbe'] = {
                    'httpGet': {'path': '/health', 'port': port},
                    'initialDelaySeconds': 30, 'periodSeconds': 10
                }
                self.fixes_applied.append(K8sFix(
                    resource=doc.get('metadata', {}).get('name', 'unknown'),
                    issue="Missing livenessProbe", fix="Added HTTP liveness probe",
                    severity="high"))
        if 'securityContext' not in spec:
            spec['securityContext'] = {
                'runAsNonRoot': True,
                'seccompProfile': {'type': 'RuntimeDefault'}
            }
        return doc
    
    def _fix_service(self, doc: Dict) -> Dict:
        spec = doc.setdefault('spec', {})
        if 'selector' not in spec or not spec['selector']:
            spec['selector'] = {'app': 'default-app'}
            self.fixes_applied.append(K8sFix(
                resource=doc.get('metadata', {}).get('name', 'unknown'),
                issue="Missing selector", fix="Added default selector",
                severity="critical"))
        return doc
    
    def _fix_ingress(self, doc: Dict) -> Dict:
        spec = doc.setdefault('spec', {})
        if 'ingressClassName' not in spec:
            spec['ingressClassName'] = 'nginx'
        return doc
    
    def _fix_configmap(self, doc: Dict) -> Dict:
        if 'data' not in doc and 'binaryData' not in doc:
            doc['data'] = {}
        return doc
    
    def _apply_error_specific_fixes(self, content: str, error_context: str) -> str:
        error_lower = error_context.lower()
        if 'oomkilled' in error_lower or 'out of memory' in error_lower:
            content = self._increase_memory(content)
        if 'imagepullbackoff' in error_lower:
            content = self._fix_image_pull(content)
        if 'crashloopbackoff' in error_lower:
            self.fixes_applied.append(K8sFix(
                resource="", issue="CrashLoopBackOff",
                fix="Check application logs with kubectl logs --previous",
                severity="critical"))
        return content
    
    def _increase_memory(self, content: str) -> str:
        def double_memory(match):
            val = match.group(1)
            num = int(''.join(filter(str.isdigit, val)))
            unit = ''.join(filter(str.isalpha, val))
            return f'memory: "{num * 2}{unit}"'
        return re.sub(r'memory:\s*"([^"]+)"', double_memory, content)
    
    def _fix_image_pull(self, content: str) -> str:
        if 'imagePullPolicy' not in content:
            content = content.replace('image:', 'imagePullPolicy: Always\n        image:', 1)
            self.fixes_applied.append(K8sFix(
                resource="", issue="ImagePullBackOff",
                fix="Added imagePullPolicy: Always",
                severity="high"))
        return content