"""
Structured logging configuration
JSON 형식의 구조화된 로그를 제공합니다.
"""

import logging
import sys
from typing import Any, Dict
from pythonjsonlogger import jsonlogger

from .settings import get_settings


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """Custom JSON formatter with additional fields"""
    
    def add_fields(
        self, 
        log_record: Dict[str, Any], 
        record: logging.LogRecord, 
        message_dict: Dict[str, Any]
    ) -> None:
        """Add custom fields to log record"""
        super().add_fields(log_record, record, message_dict)
        
        # Add environment
        settings = get_settings()
        log_record["environment"] = settings.environment
        log_record["service"] = settings.app_name
        
        # Add log level name
        if not log_record.get("level"):
            log_record["level"] = record.levelname


def setup_logging() -> logging.Logger:
    """
    Setup application logging
    
    Returns:
        logging.Logger: Configured logger
    """
    settings = get_settings()
    
    # Create logger
    logger = logging.getLogger("policy_qa_agent")
    logger.setLevel(logging.DEBUG if settings.debug else logging.INFO)
    
    # Remove existing handlers
    logger.handlers.clear()
    
    # Create console handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.DEBUG if settings.debug else logging.INFO)
    
    # Set JSON formatter
    formatter = CustomJsonFormatter(
        "%(timestamp)s %(level)s %(name)s %(message)s",
        rename_fields={"timestamp": "@timestamp"}
    )
    handler.setFormatter(formatter)
    
    # Add handler to logger
    logger.addHandler(handler)
    
    # Prevent propagation to root logger
    logger.propagate = False
    
    return logger


# Create global logger instance
logger = setup_logging()


def get_logger() -> logging.Logger:
    """
    Get logger instance
    
    Returns:
        logging.Logger: Logger instance
    """
    return logger

