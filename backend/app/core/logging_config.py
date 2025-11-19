"""
Comprehensive logging configuration with structured logging and performance monitoring.
Provides centralized logging setup for the entire application.
"""

import logging
import logging.config
import sys
import json
import time
from typing import Any, Dict, Optional
from datetime import datetime
from pathlib import Path
import traceback
from contextlib import contextmanager

from app.core.config import settings


class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured JSON logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as structured JSON."""
        
        # Base log data
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add exception information if present
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": traceback.format_exception(*record.exc_info)
            }
        
        # Add extra fields from the log record
        extra_fields = {}
        for key, value in record.__dict__.items():
            if key not in {
                'name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 'filename',
                'module', 'lineno', 'funcName', 'created', 'msecs', 'relativeCreated',
                'thread', 'threadName', 'processName', 'process', 'getMessage',
                'exc_info', 'exc_text', 'stack_info', 'message'
            }:
                extra_fields[key] = value
        
        if extra_fields:
            log_data["extra"] = extra_fields
        
        return json.dumps(log_data, default=str, ensure_ascii=False)


class PerformanceLogger:
    """Logger for performance monitoring and metrics."""
    
    def __init__(self, logger_name: str = "performance"):
        self.logger = logging.getLogger(logger_name)
        self.operation_times: Dict[str, list] = {}
    
    @contextmanager
    def time_operation(self, operation_name: str, **context):
        """Context manager to time operations."""
        start_time = time.time()
        start_timestamp = datetime.utcnow()
        
        try:
            yield
            success = True
            error = None
        except Exception as e:
            success = False
            error = str(e)
            raise
        finally:
            end_time = time.time()
            duration = end_time - start_time
            
            # Store timing for statistics
            if operation_name not in self.operation_times:
                self.operation_times[operation_name] = []
            self.operation_times[operation_name].append(duration)
            
            # Keep only last 100 measurements per operation
            if len(self.operation_times[operation_name]) > 100:
                self.operation_times[operation_name] = self.operation_times[operation_name][-100:]
            
            # Log performance data
            self.logger.info(
                f"Operation completed: {operation_name}",
                extra={
                    "operation": operation_name,
                    "duration_seconds": round(duration, 4),
                    "start_time": start_timestamp.isoformat(),
                    "success": success,
                    "error": error,
                    **context
                }
            )
    
    def get_operation_stats(self, operation_name: str) -> Optional[Dict[str, float]]:
        """Get statistics for a specific operation."""
        if operation_name not in self.operation_times:
            return None
        
        times = self.operation_times[operation_name]
        if not times:
            return None
        
        return {
            "count": len(times),
            "avg_duration": sum(times) / len(times),
            "min_duration": min(times),
            "max_duration": max(times),
            "total_duration": sum(times)
        }
    
    def get_all_stats(self) -> Dict[str, Dict[str, float]]:
        """Get statistics for all operations."""
        return {
            operation: self.get_operation_stats(operation)
            for operation in self.operation_times.keys()
        }


class SecurityLogger:
    """Logger for security-related events."""
    
    def __init__(self, logger_name: str = "security"):
        self.logger = logging.getLogger(logger_name)
    
    def log_authentication_attempt(
        self,
        user_id: Optional[str] = None,
        email: Optional[str] = None,
        success: bool = False,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        failure_reason: Optional[str] = None
    ):
        """Log authentication attempts."""
        self.logger.info(
            f"Authentication {'successful' if success else 'failed'}",
            extra={
                "event_type": "authentication",
                "user_id": user_id,
                "email": email,
                "success": success,
                "ip_address": ip_address,
                "user_agent": user_agent,
                "failure_reason": failure_reason
            }
        )
    
    def log_file_upload(
        self,
        user_id: Optional[str] = None,
        filename: Optional[str] = None,
        file_size: Optional[int] = None,
        file_type: Optional[str] = None,
        success: bool = False,
        ip_address: Optional[str] = None
    ):
        """Log file upload events."""
        self.logger.info(
            f"File upload {'successful' if success else 'failed'}",
            extra={
                "event_type": "file_upload",
                "user_id": user_id,
                "filename": filename,
                "file_size": file_size,
                "file_type": file_type,
                "success": success,
                "ip_address": ip_address
            }
        )
    
    def log_data_access(
        self,
        user_id: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        action: Optional[str] = None,
        success: bool = False,
        ip_address: Optional[str] = None
    ):
        """Log data access events."""
        self.logger.info(
            f"Data access: {action} on {resource_type}",
            extra={
                "event_type": "data_access",
                "user_id": user_id,
                "resource_type": resource_type,
                "resource_id": resource_id,
                "action": action,
                "success": success,
                "ip_address": ip_address
            }
        )


def setup_logging(
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    enable_json_logging: bool = True,
    enable_console_logging: bool = True
) -> None:
    """
    Set up comprehensive logging configuration.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional log file path
        enable_json_logging: Whether to use structured JSON logging
        enable_console_logging: Whether to log to console
    """
    
    # Create logs directory if logging to file
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Configure formatters
    if enable_json_logging:
        formatter = StructuredFormatter()
    else:
        formatter = logging.Formatter(
            fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
    
    # Configure handlers
    handlers = []
    
    if enable_console_logging:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        handlers.append(console_handler)
    
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        handlers.append(file_handler)
    
    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        handlers=handlers,
        force=True
    )
    
    # Configure specific loggers
    loggers_config = {
        "app": log_level,
        "uvicorn": "INFO",
        "uvicorn.access": "INFO",
        "sqlalchemy.engine": "WARNING",  # Reduce SQL query noise
        "httpx": "WARNING",  # Reduce HTTP client noise
        "sentence_transformers": "WARNING",  # Reduce model loading noise
        "transformers": "ERROR",  # Reduce transformer library noise
        "anthropic": "INFO",
        "redis": "WARNING"
    }
    
    for logger_name, level in loggers_config.items():
        logger = logging.getLogger(logger_name)
        logger.setLevel(getattr(logging, level.upper()))
    
    # Log configuration completion
    logger = logging.getLogger(__name__)
    logger.info(
        "Logging configuration completed",
        extra={
            "log_level": log_level,
            "log_file": log_file,
            "json_logging": enable_json_logging,
            "console_logging": enable_console_logging
        }
    )


def get_logger(name: str) -> logging.Logger:
    """Get a configured logger instance."""
    return logging.getLogger(name)


# Global logger instances
performance_logger = PerformanceLogger()
security_logger = SecurityLogger()


# Logging configuration based on environment
def configure_app_logging():
    """Configure logging for the application based on settings."""
    
    # Determine log level
    log_level = getattr(settings, 'LOG_LEVEL', 'INFO')
    
    # Determine if we're in development
    is_development = getattr(settings, 'ENVIRONMENT', 'development') == 'development'
    
    # Configure logging
    setup_logging(
        log_level=log_level,
        log_file="logs/app.log" if not is_development else None,
        enable_json_logging=not is_development,  # Use JSON in production
        enable_console_logging=True
    )


# Health check logger for monitoring
class HealthCheckLogger:
    """Logger for health check and monitoring events."""
    
    def __init__(self, logger_name: str = "health"):
        self.logger = logging.getLogger(logger_name)
    
    def log_service_health(
        self,
        service_name: str,
        status: str,
        response_time: Optional[float] = None,
        error: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """Log service health check results."""
        self.logger.info(
            f"Health check: {service_name} - {status}",
            extra={
                "event_type": "health_check",
                "service_name": service_name,
                "status": status,
                "response_time": response_time,
                "error": error,
                "details": details or {}
            }
        )
    
    def log_system_metrics(
        self,
        cpu_usage: Optional[float] = None,
        memory_usage: Optional[float] = None,
        disk_usage: Optional[float] = None,
        active_connections: Optional[int] = None
    ):
        """Log system performance metrics."""
        self.logger.info(
            "System metrics collected",
            extra={
                "event_type": "system_metrics",
                "cpu_usage": cpu_usage,
                "memory_usage": memory_usage,
                "disk_usage": disk_usage,
                "active_connections": active_connections
            }
        )


# Global health check logger
health_logger = HealthCheckLogger()