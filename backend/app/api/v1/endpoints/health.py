"""
Health check and monitoring endpoints.
Provides comprehensive system health monitoring and diagnostics.
"""

import asyncio
import time
import psutil
from typing import Dict, Any, List
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.core.deps import get_db
from app.core.logging_config import health_logger, performance_logger
from app.core.error_handler import error_handler
from app.services.embedding_service import get_embedding_service
from app.services.explanation_service import get_explanation_service
from app.schemas.health import (
    HealthCheckResponse, ServiceStatus, SystemMetrics, 
    DetailedHealthResponse, ServiceHealthCheck
)

router = APIRouter()


@router.get("/health", response_model=HealthCheckResponse)
async def basic_health_check():
    """Basic health check endpoint for load balancers."""
    return HealthCheckResponse(
        status="healthy",
        timestamp=datetime.utcnow(),
        service="resume-job-matching",
        version="1.0.0"
    )


@router.get("/health/detailed", response_model=DetailedHealthResponse)
async def detailed_health_check(db: AsyncSession = Depends(get_db)):
    """Comprehensive health check with service status details."""
    
    start_time = time.time()
    services = []
    overall_status = "healthy"
    
    # Check database connectivity
    db_status = await _check_database_health(db)
    services.append(db_status)
    if db_status.status != "healthy":
        overall_status = "degraded"
    
    # Check embedding service
    embedding_status = await _check_embedding_service_health()
    services.append(embedding_status)
    if embedding_status.status != "healthy":
        overall_status = "degraded"
    
    # Check explanation service
    explanation_status = await _check_explanation_service_health()
    services.append(explanation_status)
    if explanation_status.status != "healthy":
        overall_status = "degraded"
    
    # Check Redis connectivity
    redis_status = await _check_redis_health()
    services.append(redis_status)
    if redis_status.status != "healthy":
        overall_status = "degraded"
    
    # Get system metrics
    system_metrics = await _get_system_metrics()
    
    # Calculate total response time
    total_response_time = time.time() - start_time
    
    # Log health check results
    health_logger.log_service_health(
        service_name="system",
        status=overall_status,
        response_time=total_response_time,
        details={
            "services_checked": len(services),
            "healthy_services": len([s for s in services if s.status == "healthy"])
        }
    )
    
    return DetailedHealthResponse(
        status=overall_status,
        timestamp=datetime.utcnow(),
        service="resume-job-matching",
        version="1.0.0",
        response_time=total_response_time,
        services=services,
        system_metrics=system_metrics
    )


@router.get("/health/database")
async def database_health_check(db: AsyncSession = Depends(get_db)):
    """Specific database health check."""
    db_status = await _check_database_health(db)
    
    if db_status.status != "healthy":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=db_status.dict()
        )
    
    return db_status


@router.get("/health/services")
async def services_health_check():
    """Check health of all AI services."""
    
    services = []
    
    # Check all services concurrently
    embedding_task = _check_embedding_service_health()
    explanation_task = _check_explanation_service_health()
    redis_task = _check_redis_health()
    
    results = await asyncio.gather(
        embedding_task,
        explanation_task,
        redis_task,
        return_exceptions=True
    )
    
    for result in results:
        if isinstance(result, ServiceHealthCheck):
            services.append(result)
        else:
            # Handle exceptions
            services.append(ServiceHealthCheck(
                name="unknown_service",
                status="unhealthy",
                response_time=0.0,
                error=str(result)
            ))
    
    overall_healthy = all(s.status == "healthy" for s in services)
    
    return {
        "status": "healthy" if overall_healthy else "degraded",
        "services": services,
        "timestamp": datetime.utcnow()
    }


@router.get("/metrics")
async def get_system_metrics():
    """Get detailed system performance metrics."""
    
    metrics = await _get_system_metrics()
    
    # Add performance statistics
    performance_stats = performance_logger.get_all_stats()
    error_stats = error_handler.get_error_stats()
    
    return {
        "system_metrics": metrics,
        "performance_stats": performance_stats,
        "error_stats": error_stats,
        "timestamp": datetime.utcnow()
    }


@router.get("/metrics/performance")
async def get_performance_metrics():
    """Get performance metrics for operations."""
    return {
        "performance_stats": performance_logger.get_all_stats(),
        "timestamp": datetime.utcnow()
    }


@router.get("/metrics/errors")
async def get_error_metrics():
    """Get error statistics and monitoring data."""
    return {
        "error_stats": error_handler.get_error_stats(),
        "timestamp": datetime.utcnow()
    }


@router.post("/metrics/reset")
async def reset_metrics():
    """Reset performance and error metrics (admin only)."""
    error_handler.reset_error_stats()
    performance_logger.operation_times.clear()
    
    return {
        "message": "Metrics reset successfully",
        "timestamp": datetime.utcnow()
    }


@router.get("/monitoring/status")
async def get_monitoring_status():
    """Get monitoring service status."""
    from app.services.monitoring_service import monitoring_service
    return monitoring_service.get_monitoring_status()


@router.get("/monitoring/alerts")
async def get_active_alerts():
    """Get active monitoring alerts."""
    from app.services.monitoring_service import monitoring_service
    return {
        "active_alerts": monitoring_service.get_active_alerts(),
        "timestamp": datetime.utcnow()
    }


@router.get("/monitoring/alerts/history")
async def get_alert_history(limit: int = 50):
    """Get alert history."""
    from app.services.monitoring_service import monitoring_service
    return {
        "alert_history": monitoring_service.get_alert_history(limit),
        "timestamp": datetime.utcnow()
    }


@router.get("/monitoring/report")
async def get_health_report():
    """Generate comprehensive health report."""
    from app.services.monitoring_service import monitoring_service
    return await monitoring_service.generate_health_report()


@router.post("/monitoring/start")
async def start_monitoring():
    """Start the monitoring service."""
    from app.services.monitoring_service import monitoring_service
    await monitoring_service.start_monitoring()
    return {
        "message": "Monitoring service started",
        "timestamp": datetime.utcnow()
    }


@router.post("/monitoring/stop")
async def stop_monitoring():
    """Stop the monitoring service."""
    from app.services.monitoring_service import monitoring_service
    await monitoring_service.stop_monitoring()
    return {
        "message": "Monitoring service stopped",
        "timestamp": datetime.utcnow()
    }


async def _check_database_health(db: AsyncSession) -> ServiceHealthCheck:
    """Check database connectivity and performance."""
    
    start_time = time.time()
    
    try:
        # Simple connectivity test
        result = await db.execute(text("SELECT 1"))
        result.fetchone()
        
        response_time = time.time() - start_time
        
        # Additional checks
        details = {}
        
        # Check connection pool status if available
        try:
            pool = db.get_bind().pool
            details.update({
                "pool_size": pool.size(),
                "checked_in": pool.checkedin(),
                "checked_out": pool.checkedout(),
                "overflow": pool.overflow(),
                "invalid": pool.invalid()
            })
        except Exception:
            pass
        
        health_logger.log_service_health(
            service_name="database",
            status="healthy",
            response_time=response_time
        )
        
        return ServiceHealthCheck(
            name="database",
            status="healthy",
            response_time=response_time,
            details=details
        )
        
    except Exception as e:
        response_time = time.time() - start_time
        error_msg = str(e)
        
        health_logger.log_service_health(
            service_name="database",
            status="unhealthy",
            response_time=response_time,
            error=error_msg
        )
        
        return ServiceHealthCheck(
            name="database",
            status="unhealthy",
            response_time=response_time,
            error=error_msg
        )


async def _check_embedding_service_health() -> ServiceHealthCheck:
    """Check embedding service health."""
    
    start_time = time.time()
    
    try:
        embedding_service = await get_embedding_service()
        
        # Test embedding generation with small text
        test_text = "health check test"
        embedding = await embedding_service.generate_embedding(test_text)
        
        response_time = time.time() - start_time
        
        # Get service stats
        stats = await embedding_service.get_embedding_stats()
        
        health_logger.log_service_health(
            service_name="embedding_service",
            status="healthy",
            response_time=response_time,
            details=stats
        )
        
        return ServiceHealthCheck(
            name="embedding_service",
            status="healthy",
            response_time=response_time,
            details=stats
        )
        
    except Exception as e:
        response_time = time.time() - start_time
        error_msg = str(e)
        
        health_logger.log_service_health(
            service_name="embedding_service",
            status="unhealthy",
            response_time=response_time,
            error=error_msg
        )
        
        return ServiceHealthCheck(
            name="embedding_service",
            status="unhealthy",
            response_time=response_time,
            error=error_msg
        )


async def _check_explanation_service_health() -> ServiceHealthCheck:
    """Check explanation service health."""
    
    start_time = time.time()
    
    try:
        explanation_service = await get_explanation_service()
        
        # Get service stats (lightweight check)
        stats = await explanation_service.get_explanation_stats()
        
        response_time = time.time() - start_time
        
        health_logger.log_service_health(
            service_name="explanation_service",
            status="healthy",
            response_time=response_time,
            details=stats
        )
        
        return ServiceHealthCheck(
            name="explanation_service",
            status="healthy",
            response_time=response_time,
            details=stats
        )
        
    except Exception as e:
        response_time = time.time() - start_time
        error_msg = str(e)
        
        health_logger.log_service_health(
            service_name="explanation_service",
            status="unhealthy",
            response_time=response_time,
            error=error_msg
        )
        
        return ServiceHealthCheck(
            name="explanation_service",
            status="unhealthy",
            response_time=response_time,
            error=error_msg
        )


async def _check_redis_health() -> ServiceHealthCheck:
    """Check Redis connectivity and performance."""
    
    start_time = time.time()
    
    try:
        # Try to get embedding service to test Redis indirectly
        embedding_service = await get_embedding_service()
        
        if embedding_service._redis_client:
            # Test Redis connectivity
            await embedding_service._redis_client.ping()
            
            # Get Redis info
            info = await embedding_service._redis_client.info()
            details = {
                "connected_clients": info.get("connected_clients", 0),
                "used_memory_human": info.get("used_memory_human", "unknown"),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0)
            }
        else:
            details = {"status": "not_configured"}
        
        response_time = time.time() - start_time
        
        health_logger.log_service_health(
            service_name="redis",
            status="healthy",
            response_time=response_time,
            details=details
        )
        
        return ServiceHealthCheck(
            name="redis",
            status="healthy",
            response_time=response_time,
            details=details
        )
        
    except Exception as e:
        response_time = time.time() - start_time
        error_msg = str(e)
        
        health_logger.log_service_health(
            service_name="redis",
            status="unhealthy",
            response_time=response_time,
            error=error_msg
        )
        
        return ServiceHealthCheck(
            name="redis",
            status="unhealthy",
            response_time=response_time,
            error=error_msg
        )


async def _get_system_metrics() -> SystemMetrics:
    """Get system performance metrics."""
    
    try:
        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=1)
        
        # Memory usage
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        memory_available = memory.available
        memory_total = memory.total
        
        # Disk usage
        disk = psutil.disk_usage('/')
        disk_percent = (disk.used / disk.total) * 100
        disk_free = disk.free
        disk_total = disk.total
        
        # Network stats
        network = psutil.net_io_counters()
        
        # Process info
        process = psutil.Process()
        process_memory = process.memory_info()
        
        metrics = SystemMetrics(
            cpu_usage_percent=cpu_percent,
            memory_usage_percent=memory_percent,
            memory_available_bytes=memory_available,
            memory_total_bytes=memory_total,
            disk_usage_percent=disk_percent,
            disk_free_bytes=disk_free,
            disk_total_bytes=disk_total,
            network_bytes_sent=network.bytes_sent,
            network_bytes_received=network.bytes_recv,
            process_memory_rss=process_memory.rss,
            process_memory_vms=process_memory.vms,
            timestamp=datetime.utcnow()
        )
        
        # Log system metrics
        health_logger.log_system_metrics(
            cpu_usage=cpu_percent,
            memory_usage=memory_percent,
            disk_usage=disk_percent
        )
        
        return metrics
        
    except Exception as e:
        # Return minimal metrics if collection fails
        return SystemMetrics(
            cpu_usage_percent=0.0,
            memory_usage_percent=0.0,
            memory_available_bytes=0,
            memory_total_bytes=0,
            disk_usage_percent=0.0,
            disk_free_bytes=0,
            disk_total_bytes=0,
            network_bytes_sent=0,
            network_bytes_received=0,
            process_memory_rss=0,
            process_memory_vms=0,
            timestamp=datetime.utcnow(),
            error=str(e)
        )