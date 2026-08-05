"""Tests for Log Parser"""
import pytest
from src.parsers.log_parser import LogParser, CIPlatform

class TestLogParser:
    @pytest.fixture
    def parser(self):
        return LogParser()

    def test_detect_platform_github_actions(self, parser):
        log = "::error::Something went wrong\n::group::Build\n::endgroup::"
        platform = parser.detect_platform(log)
        assert platform == CIPlatform.GITHUB_ACTIONS

    def test_detect_platform_jenkins(self, parser):
        log = "[Pipeline] stage\nBuilding in workspace /var/jenkins\nFinished: FAILURE"
        platform = parser.detect_platform(log)
        assert platform == CIPlatform.JENKINS

    def test_detect_platform_unknown(self, parser):
        log = "Some random log content without CI markers"
        platform = parser.detect_platform(log)
        assert platform == CIPlatform.UNKNOWN

    def test_parse_github_actions_log(self, parser):
        log = """2024-01-15T10:30:00.1234567Z ##[group]Run npm test
2024-01-15T10:30:01.1234567Z > app@1.0.0 test
2024-01-15T10:30:02.1234567Z Error: Cannot find module 'express'
2024-01-15T10:30:03.1234567Z ##[error]Process completed with exit code 1.
2024-01-15T10:30:04.1234567Z ##[endgroup]"""
        result = parser.parse(log)
        assert result.platform == CIPlatform.GITHUB_ACTIONS
        assert result.status == "failure"
        assert len(result.errors) > 0

    def test_extract_docker_errors(self, parser):
        log = "docker build failed: pull access denied for myimage:latest"
        result = parser.parse(log)
        error_types = [e["type"] for e in result.errors]
        assert "docker" in error_types

    def test_extract_kubernetes_errors(self, parser):
        log = "pod myapp-12345 is in CrashLoopBackOff state"
        result = parser.parse(log)
        error_types = [e["type"] for e in result.errors]
        assert "kubernetes" in error_types

    def test_extract_terraform_errors(self, parser):
        log = "terraform apply failed: Error acquiring the state lock"
        result = parser.parse(log)
        error_types = [e["type"] for e in result.errors]
        assert "terraform" in error_types