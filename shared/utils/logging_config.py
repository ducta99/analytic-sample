"""
Structured logging configuration for all services.

Provides centralized logging with JSON output, request tracking, and correlation IDs.
"""

import json
import logging
import logging.config
import sys
from typing import Optional, Any, Dict
import uuid
from datetime import datetime
from pythonjsonlogger import jsonlogger
from contextlib import contextmanager
import threading

# Thread-local storage for request context
_request_context = threading.local()


def get_request_id() -> str:
    """Get the current request ID from context."""
    if not hasattr(_request_context, 'request_id'):
        _request_context.request_id = str(uuid.uuid4())
    return _request_context.request_id


def set_request_id(request_id: str) -> None:
    """Set the request ID for the current context."""
    _request_context.request_id = request_id


def get_request_context() -> Dict[str, Any]:
    """Get the current request context."""
    return getattr(_request_context, 'context', {})


def set_request_context(context: Dict[str, Any]) -> None:
    """Set the request context."""
    _request_context.context = context


@contextmanager
def request_context(request_id: Optional[str] = None, **context):
    """Context manager for request tracking."""
    old_request_id = getattr(_request_context, 'request_id', None)
    old_context = getattr(_request_context, 'context', None)
    
    try:
        set_request_id(request_id or str(uuid.uuid4()))
        set_request_context(context)
        yield
    finally:
        if old_request_id is not None:
            _request_context.request_id = old_request_id
        else:
            delattr(_request_context, 'request_id')
        
        if old_context is not None:
            _request_context.context = old_context
        else:
            if hasattr(_request_context, 'context'):
                delattr(_request_context, 'context')


class RequestIdFilter(logging.Filter):
    """Filter to add request ID to log records."""
    
    def filter(self, record: logging.LogRecord) -> bool:
        """Add request ID and context to log record."""
        record.request_id = get_request_id()
        context = get_request_context()
        record.user_id = context.get('user_id')
        record.service = context.get('service')
        record.path = context.get('path')
        return True


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """Custom JSON formatter with additional fields."""
    
    def add_fields(self, log_record: Dict, record: logging.LogRecord, message_dict: Dict) -> None:
        """Add custom fields to JSON log."""
        super().add_fields(log_record, record, message_dict)
        
        # Add standard fields
        log_record['timestamp'] = datetime.utcnow().isoformat() + 'Z'
        log_record['level'] = record.levelname
        log_record['logger'] = record.name
        log_record['request_id'] = record.request_id
        
        # Add context fields if present
        if hasattr(record, 'user_id') and record.user_id:
            log_record['user_id'] = record.user_id
        if hasattr(record, 'service') and record.service:
            log_record['service'] = record.service
        if hasattr(record, 'path') and record.path:
            log_record['path'] = record.path
        
        # Add exception info if present
        if record.exc_info:
            log_record['exception'] = self.formatException(record.exc_info)


def get_logger(name: str, service_name: Optional[str] = None) -> logging.Logger:
    """
    Get a configured logger with request tracking.
    
    Args:
        name: Logger name (typically __name__)
        service_name: Service identifier for the logger
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Avoid adding handlers multiple times
    if logger.handlers:
        return logger
    
    # Create console handler with JSON formatter
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    
    formatter = CustomJsonFormatter(
        fmt='%(timestamp)s %(level)s %(logger)s %(message)s',
        rename_fields={'timestamp': 'timestamp_alt'},
    )
    console_handler.setFormatter(formatter)
    
    # Add request ID filter
    request_filter = RequestIdFilter()
    console_handler.addFilter(request_filter)
    
    # Configure logger
    logger.setLevel(logging.DEBUG)
    logger.addHandler(console_handler)
    
    # Prevent propagation to root logger
    logger.propagate = False
    
    return logger


def configure_logging(log_level: str = "INFO", service_name: Optional[str] = None) -> None:
    """
    Configure logging for the application.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        service_name: Service identifier for logs
    """
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    
    formatter = CustomJsonFormatter(
        fmt='%(timestamp)s %(level)s %(logger)s %(message)s',
    )
    console_handler.setFormatter(formatter)
    
    # Add request ID filter
    request_filter = RequestIdFilter()
    console_handler.addFilter(request_filter)
    
    root_logger.addHandler(console_handler)
    
    # Suppress noisy loggers
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('kafka').setLevel(logging.WARNING)
