"""
Monitoring service for system health, performance metrics, and alerting.
"""

import asyncio
import time
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import json
from pydantic import ConfigDict
import json

from app.core.logging_config import get_logger, health_logger, performance_logger
from app.core.error_handler import error_handler

logger = get_logger(__name__)


from pydantic import BaseModel

class AlertThreshold(BaseModel):
    """Configuration for monitoring alerts."""
    metric_name: str
    warning_threshold: float
    critical_threshold: float
    check_interval: int  # seconds
    enabled: bool = True

    model_config = ConfigDict(from_attributes=True)


class MonitoringAlert(BaseModel):
    """Monitoring alert data."""
    alert_id: str
    metric_name: str
    severity: str  # warning, critical
    current_value: float
    threshold: float
    timestamp: datetime
    message: str
    resolved: bool = False

    model_config = ConfigDict(from_attributes=True)


class MonitoringService:
    """Service for system monitoring and alerting."""
    
    def __init__(self):
        self.alerts: Dict[str, MonitoringAlert] = {}
        self.alert_history: List[MonitoringAlert] = []
        self.monitoring_active = False
        self.monitoring_task: Optional[asyncio.Task] = None
        
        # Default alert thresholds
        self.thresholds = {
            "cpu_usage": AlertThreshold(metric_name="cpu_usage", warning_threshold=80.0, critical_threshold=95.0, check_interval=60),
            "memory_usage": AlertThreshold(metric_name="memory_usage", warning_threshold=85.0, critical_threshold=95.0, check_interval=60),
            "disk_usage": AlertThreshold(metric_name="disk_usage", warning_threshold=85.0, critical_threshold=95.0, check_interval=300),
            "error_rate": AlertThreshold(metric_name="error_rate", warning_threshold=5.0, critical_threshold=10.0, check_interval=60),
            "response_time": AlertThreshold(metric_name="response_time", warning_threshold=2.0, critical_threshold=5.0, check_interval=60),
            "failed_requests": AlertThreshold(metric_name="failed_requests", warning_threshold=10.0, critical_threshold=25.0, check_interval=60)
        }
    
    async def start_monitoring(self):
        """Start the monitoring service."""
        if self.monitoring_active:
            logger.warning("Monitoring service is already active")
            return
        
        self.monitoring_active = True
        self.monitoring_task = asyncio.create_task(self._monitoring_loop())
        logger.info("Monitoring service started")
    
    async def stop_monitoring(self):
        """Stop the monitoring service."""
        if not self.monitoring_active:
            return
        
        self.monitoring_active = False
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Monitoring service stopped")
    
    async def _monitoring_loop(self):
        """Main monitoring loop."""
        logger.info("Starting monitoring loop")
        
        while self.monitoring_active:
            try:
                await self._check_all_metrics()
                await asyncio.sleep(30)  # Check every 30 seconds
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(60)  # Wait longer on error
    
    async def _check_all_metrics(self):
        """Check all monitored metrics."""
        try:
            # Get system metrics
            from app.api.v1.endpoints.health import _get_system_metrics
            system_metrics = await _get_system_metrics()
            
            # Check CPU usage
            await self._check_threshold(
                "cpu_usage",
                system_metrics.cpu_usage_percent,
                "CPU usage is high"
            )
            
            # Check memory usage
            await self._check_threshold(
                "memory_usage",
                system_metrics.memory_usage_percent,
                "Memory usage is high"
            )
            
            # Check disk usage
            await self._check_threshold(
                "disk_usage",
                system_metrics.disk_usage_percent,
                "Disk usage is high"
            )
            
            # Check error rates
            error_stats = error_handler.get_error_stats()
            total_errors = error_stats.get("total_errors", 0)
            
            # Calculate error rate (errors per minute)
            error_rate = total_errors / 60.0  # Simplified calculation
            await self._check_threshold(
                "error_rate",
                error_rate,
                "Error rate is elevated"
            )
            
            # Check performance metrics
            perf_stats = performance_logger.get_all_stats()
            if perf_stats:
                # Calculate average response time across all operations
                total_ops = sum(stats["count"] for stats in perf_stats.values() if stats)
                total_time = sum(stats["total_duration"] for stats in perf_stats.values() if stats)
                
                if total_ops > 0:
                    avg_response_time = total_time / total_ops
                    await self._check_threshold(
                        "response_time",
                        avg_response_time,
                        "Average response time is high"
                    )
            
        except Exception as e:
            logger.error(f"Error checking metrics: {e}")
    
    async def _check_threshold(self, metric_name: str, current_value: float, message: str):
        """Check if a metric exceeds thresholds."""
        threshold_config = self.thresholds.get(metric_name)
        if not threshold_config or not threshold_config.enabled:
            return
        
        alert_id = f"{metric_name}_alert"
        severity = None
        threshold_value = None
        
        # Determine severity
        if current_value >= threshold_config.critical_threshold:
            severity = "critical"
            threshold_value = threshold_config.critical_threshold
        elif current_value >= threshold_config.warning_threshold:
            severity = "warning"
            threshold_value = threshold_config.warning_threshold
        
        if severity:
            # Create or update alert
            if alert_id not in self.alerts or self.alerts[alert_id].resolved:
                alert = MonitoringAlert(
                    alert_id=alert_id,
                    metric_name=metric_name,
                    severity=severity,
                    current_value=current_value,
                    threshold=threshold_value,
                    timestamp=datetime.utcnow(),
                    message=f"{message}: {current_value:.2f} (threshold: {threshold_value:.2f})"
                )
                
                self.alerts[alert_id] = alert
                self.alert_history.append(alert)
                
                # Log alert
                logger.warning(
                    f"ALERT [{severity.upper()}]: {alert.message}",
                    extra={
                        "alert_id": alert_id,
                        "metric_name": metric_name,
                        "severity": severity,
                        "current_value": current_value,
                        "threshold": threshold_value
                    }
                )
                
                # Log to health logger
                health_logger.log_service_health(
                    service_name="monitoring",
                    status="alert",
                    details={
                        "alert_type": severity,
                        "metric": metric_name,
                        "value": current_value,
                        "threshold": threshold_value
                    }
                )
        else:
            # Resolve alert if it exists
            if alert_id in self.alerts and not self.alerts[alert_id].resolved:
                self.alerts[alert_id].resolved = True
                logger.info(
                    f"RESOLVED: {metric_name} alert - value: {current_value:.2f}",
                    extra={
                        "alert_id": alert_id,
                        "metric_name": metric_name,
                        "current_value": current_value
                    }
                )
    
    def get_active_alerts(self) -> List[Dict[str, Any]]:
        """Get all active alerts."""
        active_alerts = [
            alert.model_dump() for alert in self.alerts.values()
            if not alert.resolved
        ]
        
        # Convert datetime to string for JSON serialization
        for alert in active_alerts:
            alert["timestamp"] = alert["timestamp"].isoformat()
        
        return active_alerts
    
    def get_alert_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get alert history."""
        recent_alerts = self.alert_history[-limit:] if limit else self.alert_history
        
        alerts_data = [alert.model_dump() for alert in recent_alerts]
        
        # Convert datetime to string for JSON serialization
        for alert in alerts_data:
            alert["timestamp"] = alert["timestamp"].isoformat()
        
        return alerts_data
    
    def update_threshold(self, metric_name: str, warning: float, critical: float):
        """Update alert threshold for a metric."""
        if metric_name in self.thresholds:
            self.thresholds[metric_name].warning_threshold = warning
            self.thresholds[metric_name].critical_threshold = critical
            logger.info(f"Updated thresholds for {metric_name}: warning={warning}, critical={critical}")
        else:
            logger.warning(f"Unknown metric for threshold update: {metric_name}")
    
    def enable_metric_monitoring(self, metric_name: str, enabled: bool = True):
        """Enable or disable monitoring for a specific metric."""
        if metric_name in self.thresholds:
            self.thresholds[metric_name].enabled = enabled
            status = "enabled" if enabled else "disabled"
            logger.info(f"Monitoring for {metric_name} {status}")
        else:
            logger.warning(f"Unknown metric: {metric_name}")
    
    def get_monitoring_status(self) -> Dict[str, Any]:
        """Get current monitoring status."""
        return {
            "monitoring_active": self.monitoring_active,
            "active_alerts_count": len([a for a in self.alerts.values() if not a.resolved]),
            "total_alerts_count": len(self.alert_history),
            "thresholds": {
                name: {
                    "warning": config.warning_threshold,
                    "critical": config.critical_threshold,
                    "enabled": config.enabled
                }
                for name, config in self.thresholds.items()
            }
        }
    
    async def generate_health_report(self) -> Dict[str, Any]:
        """Generate comprehensive health report."""
        try:
            # Get system metrics
            from app.api.v1.endpoints.health import _get_system_metrics
            system_metrics = await _get_system_metrics()
            
            # Get performance stats
            perf_stats = performance_logger.get_all_stats()
            
            # Get error stats
            error_stats = error_handler.get_error_stats()
            
            # Get active alerts
            active_alerts = self.get_active_alerts()
            
            report = {
                "timestamp": datetime.utcnow().isoformat(),
                "system_metrics": {
                    "cpu_usage_percent": system_metrics.cpu_usage_percent,
                    "memory_usage_percent": system_metrics.memory_usage_percent,
                    "disk_usage_percent": system_metrics.disk_usage_percent,
                    "process_memory_mb": system_metrics.process_memory_rss / (1024 * 1024)
                },
                "performance_summary": {
                    "total_operations": sum(stats["count"] for stats in perf_stats.values() if stats),
                    "avg_response_time": (
                        sum(stats["total_duration"] for stats in perf_stats.values() if stats) /
                        max(sum(stats["count"] for stats in perf_stats.values() if stats), 1)
                    ),
                    "slowest_operation": max(
                        (stats["max_duration"] for stats in perf_stats.values() if stats),
                        default=0
                    )
                },
                "error_summary": {
                    "total_errors": error_stats.get("total_errors", 0),
                    "error_types": len(error_stats.get("error_counts", {}))
                },
                "alerts": {
                    "active_count": len(active_alerts),
                    "active_alerts": active_alerts
                },
                "monitoring_status": self.get_monitoring_status()
            }
            
            return report
            
        except Exception as e:
            logger.error(f"Error generating health report: {e}")
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "error": f"Failed to generate report: {str(e)}"
            }


# Global monitoring service instance
monitoring_service = MonitoringService()