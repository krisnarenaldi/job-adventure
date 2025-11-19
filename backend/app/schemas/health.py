"""
Schemas for health check and monitoring endpoints.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class HealthCheckResponse(BaseModel):
    """Basic health check response."""
    status: str = Field(..., description="Health status (healthy, degraded, unhealthy)")
    timestamp: datetime = Field(..., description="Timestamp of health check")
    service: str = Field(..., description="Service name")
    version: str = Field(..., description="Service version")


class ServiceHealthCheck(BaseModel):
    """Health check result for a specific service."""
    name: str = Field(..., description="Service name")
    status: str = Field(..., description="Service status (healthy, degraded, unhealthy)")
    response_time: float = Field(..., description="Response time in seconds")
    error: Optional[str] = Field(None, description="Error message if unhealthy")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional service details")


class SystemMetrics(BaseModel):
    """System performance metrics."""
    cpu_usage_percent: float = Field(..., description="CPU usage percentage")
    memory_usage_percent: float = Field(..., description="Memory usage percentage")
    memory_available_bytes: int = Field(..., description="Available memory in bytes")
    memory_total_bytes: int = Field(..., description="Total memory in bytes")
    disk_usage_percent: float = Field(..., description="Disk usage percentage")
    disk_free_bytes: int = Field(..., description="Free disk space in bytes")
    disk_total_bytes: int = Field(..., description="Total disk space in bytes")
    network_bytes_sent: int = Field(..., description="Network bytes sent")
    network_bytes_received: int = Field(..., description="Network bytes received")
    process_memory_rss: int = Field(..., description="Process RSS memory usage")
    process_memory_vms: int = Field(..., description="Process VMS memory usage")
    timestamp: datetime = Field(..., description="Timestamp of metrics collection")
    error: Optional[str] = Field(None, description="Error message if collection failed")


class DetailedHealthResponse(BaseModel):
    """Comprehensive health check response with service details."""
    status: str = Field(..., description="Overall health status")
    timestamp: datetime = Field(..., description="Timestamp of health check")
    service: str = Field(..., description="Service name")
    version: str = Field(..., description="Service version")
    response_time: float = Field(..., description="Total health check response time")
    services: List[ServiceHealthCheck] = Field(..., description="Individual service health checks")
    system_metrics: SystemMetrics = Field(..., description="System performance metrics")


class ServiceStatus(BaseModel):
    """Service status information."""
    name: str = Field(..., description="Service name")
    status: str = Field(..., description="Service status")
    last_check: datetime = Field(..., description="Last health check timestamp")
    uptime: Optional[float] = Field(None, description="Service uptime in seconds")
    error_count: int = Field(0, description="Number of recent errors")
    
    
class PerformanceMetrics(BaseModel):
    """Performance metrics for operations."""
    operation_name: str = Field(..., description="Name of the operation")
    count: int = Field(..., description="Number of operations")
    avg_duration: float = Field(..., description="Average duration in seconds")
    min_duration: float = Field(..., description="Minimum duration in seconds")
    max_duration: float = Field(..., description="Maximum duration in seconds")
    total_duration: float = Field(..., description="Total duration in seconds")


class ErrorMetrics(BaseModel):
    """Error tracking metrics."""
    error_type: str = Field(..., description="Type of error")
    count: int = Field(..., description="Number of occurrences")
    last_occurrence: datetime = Field(..., description="Last occurrence timestamp")
    operation: Optional[str] = Field(None, description="Operation where error occurred")