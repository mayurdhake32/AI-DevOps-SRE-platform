"""Deployment Manager - Handles redeployment, health checks, and rollback"""
import os
import time
import subprocess
from typing import Dict, Optional
from enum import Enum
from dataclasses import dataclass
from src.utils.logger import get_logger

logger = get_logger(__name__)

class DeploymentStrategy(Enum):
    ROLLING = "rolling"
    BLUE_GREEN = "blue-green"
    CANARY = "canary"

@dataclass
class DeploymentResult:
    success: bool
    deployment_id: str
    duration_seconds: float
    logs: str
    health_check_passed: bool
    rollback_triggered: bool

class DeploymentManager:
    def __init__(self, strategy: DeploymentStrategy = DeploymentStrategy.ROLLING):
        self.strategy = strategy
        self.health_check_timeout = 300
        self.rollback_on_failure = True

    def deploy_kubernetes(self, namespace: str, manifest_path: str) -> DeploymentResult:
        start_time = time.time()
        deployment_id = f"k8s-{int(start_time)}"
        try:
            result = subprocess.run(
                ["kubectl", "apply", "-f", manifest_path, "-n", namespace],
                capture_output=True, text=True, timeout=120
            )
            if result.returncode != 0:
                return DeploymentResult(
                    success=False, deployment_id=deployment_id,
                    duration_seconds=time.time() - start_time,
                    logs=result.stderr, health_check_passed=False,
                    rollback_triggered=False)
            rollout_result = subprocess.run(
                ["kubectl", "rollout", "status", "deployment", "-n", namespace, "--timeout=5m"],
                capture_output=True, text=True, timeout=360
            )
            health_passed = rollout_result.returncode == 0
            if not health_passed and self.rollback_on_failure:
                self.rollback_kubernetes(namespace)
                return DeploymentResult(
                    success=False, deployment_id=deployment_id,
                    duration_seconds=time.time() - start_time,
                    logs=rollout_result.stderr, health_check_passed=False,
                    rollback_triggered=True)
            return DeploymentResult(
                success=True, deployment_id=deployment_id,
                duration_seconds=time.time() - start_time,
                logs=result.stdout + rollout_result.stdout,
                health_check_passed=health_passed, rollback_triggered=False)
        except Exception as e:
            logger.error(f"Deployment failed: {e}")
            return DeploymentResult(
                success=False, deployment_id=deployment_id,
                duration_seconds=time.time() - start_time,
                logs=str(e), health_check_passed=False,
                rollback_triggered=False)

    def rollback_kubernetes(self, namespace: str) -> bool:
        try:
            result = subprocess.run(
                ["kubectl", "rollout", "undo", "deployment", "-n", namespace],
                capture_output=True, text=True, timeout=120
            )
            return result.returncode == 0
        except Exception as e:
            logger.error(f"Rollback failed: {e}")
            return False

    def deploy_docker_compose(self, compose_file: str) -> DeploymentResult:
        start_time = time.time()
        deployment_id = f"compose-{int(start_time)}"
        try:
            result = subprocess.run(
                ["docker-compose", "-f", compose_file, "up", "-d", "--build"],
                capture_output=True, text=True, timeout=300
            )
            success = result.returncode == 0
            return DeploymentResult(
                success=success, deployment_id=deployment_id,
                duration_seconds=time.time() - start_time,
                logs=result.stdout + result.stderr,
                health_check_passed=success, rollback_triggered=False)
        except Exception as e:
            return DeploymentResult(
                success=False, deployment_id=deployment_id,
                duration_seconds=time.time() - start_time,
                logs=str(e), health_check_passed=False,
                rollback_triggered=False)

    def health_check(self, endpoint: str, expected_status: int = 200,
                     retries: int = 10, delay: int = 5) -> bool:
        import requests
        for i in range(retries):
            try:
                response = requests.get(endpoint, timeout=10)
                if response.status_code == expected_status:
                    return True
            except Exception:
                pass
            time.sleep(delay)
        return False