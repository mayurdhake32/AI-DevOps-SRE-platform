#!/usr/bin/env python3
"""AI DevOps SRE - Main Orchestrator"""
import os
import sys
import json
import argparse
from typing import Dict, List, Optional

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from src.parsers.log_parser import LogParser, CIPlatform
from src.ml.training.error_classifier import ErrorClassifier
from src.ml.training.failure_predictor import FailurePredictor
from src.rag.knowledge_base import DevOpsKnowledgeBase
from src.agents.root_cause_analyzer import RootCauseAnalyzer
from src.fixers.yaml_fixer import YAMLFixer
from src.fixers.docker_fixer import DockerFixer
from src.fixers.k8s_fixer import K8sFixer
from src.fixers.terraform_fixer import TerraformFixer
from src.integrations.github_integration import GitHubIntegration
from src.integrations.deployment_manager import DeploymentManager
from src.utils.logger import get_logger

from dotenv import load_dotenv
load_dotenv()  # Add this at the very top of main.py and app.py

logger = get_logger(__name__)

class AIDevOpsSRE:
    def __init__(self, config_path: str = "config/settings.yaml"):
        self.config = self._load_config(config_path)
        self.log_parser = LogParser()
        self.error_classifier = ErrorClassifier()
        self.failure_predictor = FailurePredictor()
        self.knowledge_base = DevOpsKnowledgeBase()
        self.root_cause_analyzer = RootCauseAnalyzer(
            self.knowledge_base, self.error_classifier
        )
        self.yaml_fixer = YAMLFixer()
        self.docker_fixer = DockerFixer()
        self.k8s_fixer = K8sFixer()
        self.terraform_fixer = TerraformFixer()
        self.github = None
        self.deployment_manager = DeploymentManager()
        if os.getenv("GITHUB_TOKEN"):
            try:
                self.github = GitHubIntegration()
            except Exception as e:
                logger.warning(f"GitHub integration not available: {e}")

    def _load_config(self, path: str) -> Dict:
        import yaml
        try:
            with open(path) as f:
                return yaml.safe_load(f)
        except Exception:
            return {}

    def process_failed_deployment(self, log_content: str, repo_name: str,
                                   repo_context: Optional[Dict] = None) -> Dict:
        workflow_result = {"status": "started", "steps": [], "errors": []}
        ml_prediction = {'predicted_categories': [], 'confidence_scores': {}, 'primary_category': 'unknown', 'confidence': 0.0}
        parsed_log = None
        root_cause = None
        try:
            logger.info("Step 1: Parsing deployment logs")
            parsed_log = self.log_parser.parse(log_content)
            workflow_result["steps"].append({
                "step": "log_parsing", "status": "success",
                "platform": parsed_log.platform.value,
                "error_count": len(parsed_log.errors)
            })

            logger.info("Step 2: Classifying errors")
            raw_prediction = self.error_classifier.predict(parsed_log.raw_log[:5000])
            if raw_prediction is not None:
                ml_prediction = raw_prediction
            workflow_result["steps"].append({
                "step": "error_classification", "status": "success",
                "primary_error": ml_prediction.get("primary_category", "unknown"),
                "confidence": ml_prediction.get("confidence", 0.0)
            })

            logger.info("Step 3: Performing root cause analysis")
            root_cause = self.root_cause_analyzer.analyze(parsed_log, repo_context)
            workflow_result["steps"].append({
                "step": "root_cause_analysis", "status": "success",
                "category": root_cause.category.value,
                "confidence": getattr(root_cause, 'confidence', 0.0),
                "severity": root_cause.severity
            })

            logger.info("Step 4: Generating fixes")
            fixes = self._generate_fixes(root_cause, repo_name, parsed_log)
            workflow_result["steps"].append({
                "step": "fix_generation", "status": "success" if fixes else "skipped",
                "fixes_count": len(fixes)
            })

            pr_info = None
            if self.github and fixes:
                logger.info("Step 5: Creating pull request")
                pr_info = self._create_pr(repo_name, root_cause, fixes)
                workflow_result["steps"].append({
                    "step": "pr_creation", "status": "success" if pr_info else "failed",
                    "pr_url": pr_info["url"] if pr_info else None
                })

            workflow_result["status"] = "completed"
            workflow_result["root_cause"] = {
                "category": root_cause.category.value,
                "description": root_cause.description,
                "confidence": getattr(root_cause, 'confidence', 0.0),
                "severity": root_cause.severity,
                "suggested_fixes": root_cause.suggested_fixes
            }
            workflow_result["pull_request"] = pr_info

        except Exception as e:
            logger.error(f"Workflow failed: {e}", exc_info=True)
            workflow_result["status"] = "failed"
            workflow_result["errors"].append(str(e))
        return workflow_result


    def _generate_fixes(self, root_cause, repo_name: str, parsed_log) -> List[Dict]:
        fixes = []
        affected = root_cause.affected_components

        if "docker" in affected or "dockerfile" in affected:
            try:
                dockerfile_content = self.github.get_file_content(repo_name, "Dockerfile") if self.github else None
                if dockerfile_content:
                    fixed, _ = self.docker_fixer.fix_dockerfile(dockerfile_content, error_context=parsed_log.raw_log[:2000])
                    if fixed != dockerfile_content:
                        fixes.append({"file": "Dockerfile", "content": fixed,
                                      "description": "Fixed Docker configuration issues", "type": "docker"})
            except Exception as e:
                logger.error(f"Docker fix failed: {e}")

        if "kubernetes" in affected or "k8s" in affected:
            try:
                for k8s_file in ["deployment.yaml", "service.yaml", "ingress.yaml"]:
                    content = self.github.get_file_content(repo_name, k8s_file) if self.github else None
                    if content:
                        fixed, _ = self.k8s_fixer.fix_manifest(content, error_context=parsed_log.raw_log[:2000])
                        if fixed != content:
                            fixes.append({"file": k8s_file, "content": fixed,
                                          "description": "Fixed Kubernetes manifest", "type": "kubernetes"})
            except Exception as e:
                logger.error(f"K8s fix failed: {e}")

        if "terraform" in affected:
            try:
                for tf_file in ["main.tf", "variables.tf", "terraform.tfvars"]:
                    content = self.github.get_file_content(repo_name, tf_file) if self.github else None
                    if content:
                        fixed, _ = self.terraform_fixer.fix_file(content, error_context=parsed_log.raw_log[:2000])
                        if fixed != content:
                            fixes.append({"file": tf_file, "content": fixed,
                                          "description": "Fixed Terraform configuration", "type": "terraform"})
            except Exception as e:
                logger.error(f"Terraform fix failed: {e}")

        if "yaml" in affected:
            try:
                for yaml_file in ["docker-compose.yml", ".github/workflows/ci.yml"]:
                    content = self.github.get_file_content(repo_name, yaml_file) if self.github else None
                    if content:
                        fixed, _ = self.yaml_fixer.fix_file(content, error_context=parsed_log.raw_log[:2000])
                        if fixed != content:
                            fixes.append({"file": yaml_file, "content": fixed,
                                          "description": "Fixed YAML syntax and structure", "type": "yaml"})
            except Exception as e:
                logger.error(f"YAML fix failed: {e}")
        return fixes

    def _create_pr(self, repo_name: str, root_cause, fixes: List[Dict]) -> Optional[Dict]:
        if not self.github:
            return None
        branch = self.github.create_fix_branch(repo_name)
        if not branch:
            return None
        file_changes = [{"path": fix["file"], "content": fix["content"]} for fix in fixes]
        committed = self.github.commit_file_changes(
            repo_name, branch, file_changes,
            f"SRE Fix: {root_cause.category.value} - {root_cause.description[:50]}"
        )
        if not committed:
            return None
        title = f"[SRE] Fix: {root_cause.category.value.replace('_', ' ').title()}"
        body = self.github.generate_pr_description(
            {"category": root_cause.category.value, "severity": root_cause.severity,
             "confidence": root_cause.confidence, "description": root_cause.description,
             "evidence": root_cause.evidence}, fixes
        )
        return self.github.create_pull_request(repo_name, branch, title, body)

    def predict_failure(self, deployment_info: Dict) -> Dict:
        return self.failure_predictor.predict(deployment_info)

    def train_models(self, logs: List[Dict], deployments: List[Dict]) -> Dict:
        results = {}
        if logs:
            results["error_classifier"] = self.error_classifier.train(logs)
        if deployments:
            results["failure_predictor"] = self.failure_predictor.train(deployments)
        return results

def main():
    parser = argparse.ArgumentParser(description="AI DevOps SRE")
    parser.add_argument("--log-file", help="Path to CI/CD log file")
    parser.add_argument("--repo", help="GitHub repo (owner/repo)")
    parser.add_argument("--predict", action="store_true", help="Predict deployment failure")
    parser.add_argument("--train", action="store_true", help="Train models")
    parser.add_argument("--init-kb", action="store_true", help="Initialize knowledge base")
    args = parser.parse_args()

    sre = AIDevOpsSRE()

    if args.init_kb:
        sre.knowledge_base.initialize_default_knowledge()
        print("Knowledge base initialized")
        return

    if args.log_file and args.repo:
        with open(args.log_file) as f:
            log_content = f.read()
        result = sre.process_failed_deployment(log_content, args.repo)
        print(json.dumps(result, indent=2))
    elif args.predict:
        deployment_info = {
            "lines_added": 500, "lines_deleted": 100, "files_changed": 10,
            "commits_count": 3, "test_files_changed": 2, "config_files_changed": 1,
            "dependencies_changed": 1, "author_failure_rate": 0.1,
            "hour_of_day": 14, "day_of_week": 2, "avg_file_complexity": 5,
            "review_comments_count": 2, "approval_count": 1,
            "last_deployment_failed": False, "time_since_last_deployment_hours": 24
        }
        prediction = sre.predict_failure(deployment_info)
        print(json.dumps(prediction, indent=2))

if __name__ == "__main__":
    main()