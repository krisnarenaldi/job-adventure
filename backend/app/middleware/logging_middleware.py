"""
Logging middleware for request/response monitoring and performance tracking.
"""

import time
import uuid
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.logging_config import get_logger, performance_logger, security_logger

logger = get_logger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for comprehensive request/response logging."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and log details."""
        
        # Generate request ID for tracing
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # Extract client information
        client_ip = self._get_client_ip(request)
        user_agent = request.headers.get("user-agent", "unknown")
        
        # Start timing
        start_time = time.time()
        
        # Log request start
        logger.info(
            f"Request started: {request.method} {request.url.path}",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "query_params": dict(request.query_params),
                "client_ip": client_ip,
                "user_agent": user_agent,
                "content_type": request.headers.get("content-type"),
                "content_length": request.headers.get("content-length")
            }
        )
        
        # Process request
        try:
            response = await call_next(request)
            
            # Calculate processing time
            process_time = time.time() - start_time
            
            # Log successful response
            logger.info(
                f"Request completed: {request.method} {request.url.path}",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "process_time": round(process_time, 4),
                    "response_size": response.headers.get("content-length"),
                    "client_ip": client_ip
                }
            )
            
            # Log performance metrics
            with performance_logger.time_operation(
                f"http_request_{request.method.lower()}",
                path=request.url.path,
                status_code=response.status_code,
                client_ip=client_ip
            ):
                pass  # Time operation context manager handles the logging
            
            # Log security events for sensitive endpoints
            if self._is_sensitive_endpoint(request.url.path):
                security_logger.log_data_access(
                    user_id=getattr(request.state, 'user_id', None),
                    resource_type=self._get_resource_type(request.url.path),
                    action=request.method,
                    success=200 <= response.status_code < 400,
                    ip_address=client_ip
                )
            
            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id
            
            return response
            
        except Exception as e:
            # Calculate processing time for failed requests
            process_time = time.time() - start_time
            
            # Log error
            logger.error(
                f"Request failed: {request.method} {request.url.path}",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "process_time": round(process_time, 4),
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "client_ip": client_ip
                },
                exc_info=True
            )
            
            # Re-raise the exception to be handled by exception handlers
            raise
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address from request."""
        # Check for forwarded headers first (for load balancers/proxies)
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        # Fall back to direct client IP
        if request.client:
            return request.client.host
        
        return "unknown"
    
    def _is_sensitive_endpoint(self, path: str) -> bool:
        """Check if endpoint handles sensitive data."""
        sensitive_patterns = [
            "/auth/",
            "/files/",
            "/documents/",
            "/resumes/",
            "/jobs/",
            "/matching/"
        ]
        
        return any(pattern in path for pattern in sensitive_patterns)
    
    def _get_resource_type(self, path: str) -> str:
        """Extract resource type from path."""
        if "/auth/" in path:
            return "authentication"
        elif "/files/" in path or "/documents/" in path:
            return "file"
        elif "/resumes/" in path:
            return "resume"
        elif "/jobs/" in path:
            return "job"
        elif "/matching/" in path:
            return "matching"
        elif "/analytics/" in path:
            return "analytics"
        else:
            return "unknown"


class PerformanceMonitoringMiddleware(BaseHTTPMiddleware):
    """Middleware specifically for performance monitoring."""
    
    def __init__(self, app, slow_request_threshold: float = 5.0):
        super().__init__(app)
        self.slow_request_threshold = slow_request_threshold
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Monitor request performance and log slow requests."""
        
        start_time = time.time()
        
        try:
            response = await call_next(request)
            
            process_time = time.time() - start_time
            
            # Log slow requests
            if process_time > self.slow_request_threshold:
                logger.warning(
                    f"Slow request detected: {request.method} {request.url.path}",
                    extra={
                        "method": request.method,
                        "path": request.url.path,
                        "process_time": round(process_time, 4),
                        "threshold": self.slow_request_threshold,
                        "status_code": response.status_code,
                        "query_params": dict(request.query_params)
                    }
                )
            
            return response
            
        except Exception as e:
            process_time = time.time() - start_time
            
            # Log failed request performance
            logger.error(
                f"Failed request performance: {request.method} {request.url.path}",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "process_time": round(process_time, 4),
                    "error": str(e),
                    "error_type": type(e).__name__
                }
            )
            
            raise