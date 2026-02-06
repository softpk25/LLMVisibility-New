"""
Logging configuration for Prometrix backend
"""

import logging
import sys
from typing import Dict, Any
from core.config import settings


class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured logging"""
    
    def format(self, record: logging.LogRecord) -> str:
        # Add structured fields
        if not hasattr(record, 'service'):
            record.service = 'prometrix-backend'
        
        if not hasattr(record, 'component'):
            record.component = record.name
            
        return super().format(record)


def setup_logging():
    """Setup application logging"""
    
    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, settings.LOG_LEVEL.upper()),
        format=settings.LOG_FORMAT,
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Configure specific loggers
    loggers_config = {
        "uvicorn": {"level": "INFO"},
        "uvicorn.access": {"level": "INFO"},
        "fastapi": {"level": "INFO"},
        "prometrix": {"level": settings.LOG_LEVEL.upper()},
    }
    
    for logger_name, config in loggers_config.items():
        logger = logging.getLogger(logger_name)
        logger.setLevel(getattr(logging, config["level"]))
    
    # Disable some noisy loggers in production
    if not settings.DEBUG:
        logging.getLogger("urllib3").setLevel(logging.WARNING)
        logging.getLogger("httpx").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Get a logger with structured formatting"""
    return logging.getLogger(f"prometrix.{name}")