"""
Structured logging utility for AI DevOps SRE
"""
import logging
import sys
from datetime import datetime
from typing import Optional
import json

class StructuredLogFormatter(logging.Formatter):
    def format(self, record):
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        if hasattr(record, "correlation_id"):
            log_data["correlation_id"] = record.correlation_id
        if hasattr(record, "deployment_id"):
            log_data["deployment_id"] = record.deployment_id
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_data)

class SRELogger:
    _instance: Optional[logging.Logger] = None
    
    @classmethod
    def get_logger(cls, name: str = "ai-devops-sre") -> logging.Logger:
        if cls._instance is None:
            cls._instance = cls._setup_logger(name)
        return cls._instance
    
    @staticmethod
    def _setup_logger(name: str) -> logging.Logger:
        logger = logging.getLogger(name)
        logger.setLevel(logging.INFO)
        if not logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            handler.setFormatter(StructuredLogFormatter())
            logger.addHandler(handler)
        return logger

def get_logger(name: str = "ai-devops-sre") -> logging.Logger:
    return SRELogger.get_logger(name)