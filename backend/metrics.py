"""
Prometheus metrics for Biomech AI - Phase 2.10 Monitoring Setup

Implements comprehensive metrics collection for API performance, accuracy,
and operational health tracking.
"""

import logging
import time
from typing import Any, Dict

from prometheus_client import CollectorRegistry, Counter, Gauge, Histogram, Info

logger = logging.getLogger(__name__)

# Create custom registry
REGISTRY = CollectorRegistry()

# ==================== REQUEST METRICS ====================

# Counter: Total requests by endpoint and method
requests_total = Counter(
    "biomech_requests_total",
    "Total requests by endpoint and method",
    ["endpoint", "method", "status"],
    registry=REGISTRY,
)

# Histogram: Request latency in seconds
request_duration = Histogram(
    "biomech_request_duration_seconds",
    "Request duration in seconds",
    ["endpoint", "method"],
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
    registry=REGISTRY,
)

# Gauge: Concurrent active requests
active_requests = Gauge(
    "biomech_active_requests", "Number of currently active requests", registry=REGISTRY
)

# ==================== BUSINESS METRICS ====================

# Counter: Analysis requests by exercise type
analysis_requests_total = Counter(
    "biomech_analysis_requests_total",
    "Total analysis requests by exercise type",
    ["exercise_type"],
    registry=REGISTRY,
)

# Counter: AI feedback generations
ai_feedback_total = Counter(
    "biomech_ai_feedback_total",
    "Total AI feedback generations",
    ["status"],  # 'success', 'fallback', 'failed'
    registry=REGISTRY,
)

# Histogram: Analysis processing time
analysis_duration = Histogram(
    "biomech_analysis_duration_seconds",
    "Analysis processing time in seconds",
    ["exercise_type"],
    buckets=(0.1, 0.25, 0.5, 1.0, 2.5, 5.0),
    registry=REGISTRY,
)

# Counter: Risk levels detected
risk_levels = Counter(
    "biomech_risk_levels_total",
    "Risk levels detected in analysis",
    ["level"],  # 'LOW', 'MEDIUM', 'HIGH'
    registry=REGISTRY,
)

# ==================== ACCURACY METRICS ====================

# Gauge: Average pose confidence score
pose_confidence = Gauge(
    "biomech_pose_confidence", "Average pose detection confidence", registry=REGISTRY
)

# Counter: AI fallback events
ai_fallback_events = Counter(
    "biomech_ai_fallback_events_total",
    "Total times AI system fell back to safe mode",
    ["reason"],  # 'timeout', 'error', 'unavailable'
    registry=REGISTRY,
)

# ==================== CACHE METRICS ====================

# Counter: Cache hits and misses
cache_hits = Counter(
    "biomech_cache_hits_total",
    "Total cache hits",
    ["cache_type"],  # 'redis', 'memory'
    registry=REGISTRY,
)

cache_misses = Counter(
    "biomech_cache_misses_total", "Total cache misses", ["cache_type"], registry=REGISTRY
)

# Gauge: Cache size in bytes
cache_size = Gauge(
    "biomech_cache_size_bytes", "Current cache size in bytes", ["cache_type"], registry=REGISTRY
)

# Counter: Cache operations
cache_operations = Counter(
    "biomech_cache_operations_total",
    "Total cache operations",
    ["operation", "status"],  # operation: 'set', 'get', 'delete'; status: 'success', 'failed'
    registry=REGISTRY,
)

# ==================== DATABASE METRICS ====================

# Counter: Database operations
db_operations = Counter(
    "biomech_db_operations_total",
    "Total database operations",
    ["operation", "table", "status"],  # operation: 'insert', 'update', 'select'
    registry=REGISTRY,
)

# Histogram: Database query time
db_query_duration = Histogram(
    "biomech_db_query_duration_seconds",
    "Database query duration in seconds",
    ["table", "operation"],
    buckets=(0.01, 0.05, 0.1, 0.5, 1.0),
    registry=REGISTRY,
)

# ==================== ERROR METRICS ====================

# Counter: Errors by type
errors_total = Counter(
    "biomech_errors_total",
    "Total errors by type",
    ["error_type", "endpoint"],  # error_type: 'validation', 'timeout', 'rate_limit', 'server'
    registry=REGISTRY,
)

# Counter: 4xx and 5xx status codes
http_errors = Counter(
    "biomech_http_errors_total", "HTTP errors by status code", ["status_code"], registry=REGISTRY
)

# ==================== BACKGROUND TASK METRICS ====================

# Counter: Task submissions
background_tasks_submitted = Counter(
    "biomech_background_tasks_submitted_total",
    "Total background tasks submitted",
    ["operation"],
    registry=REGISTRY,
)

# Counter: Task completions
background_tasks_completed = Counter(
    "biomech_background_tasks_completed_total",
    "Total background tasks completed",
    ["operation", "status"],  # status: 'success', 'failed'
    registry=REGISTRY,
)

# Gauge: Active background tasks
active_background_tasks = Gauge(
    "biomech_active_background_tasks",
    "Number of currently active background tasks",
    registry=REGISTRY,
)

# ==================== EXTERNAL SERVICE METRICS ====================

# Counter: Gemini API calls
gemini_api_calls = Counter(
    "biomech_gemini_api_calls_total",
    "Total Gemini API calls",
    ["status"],  # 'success', 'timeout', 'error'
    registry=REGISTRY,
)

# Histogram: Gemini API response time
gemini_api_duration = Histogram(
    "biomech_gemini_api_duration_seconds",
    "Gemini API response time in seconds",
    buckets=(0.5, 1.0, 2.0, 5.0, 10.0),
    registry=REGISTRY,
)

# Counter: Supabase operations
supabase_operations = Counter(
    "biomech_supabase_operations_total",
    "Total Supabase operations",
    ["operation", "status"],  # operation: 'insert', 'select', 'update'
    registry=REGISTRY,
)

# ==================== RATE LIMITING METRICS ====================

# Counter: Rate limit hits
rate_limit_hits = Counter(
    "biomech_rate_limit_hits_total", "Total rate limit violations", ["endpoint"], registry=REGISTRY
)

# ==================== APPLICATION INFO ====================

app_info = Info("biomech_app", "Biomech AI Application Info", registry=REGISTRY)

# ==================== UTILITY FUNCTIONS ====================


class MetricsCollector:
    """Helper class for recording metrics"""

    @staticmethod
    def record_request(endpoint: str, method: str, status: int, duration: float):
        """Record HTTP request metrics"""
        requests_total.labels(endpoint=endpoint, method=method, status=status).inc()
        request_duration.labels(endpoint=endpoint, method=method).observe(duration)
        if status >= 400:
            http_errors.labels(status_code=status).inc()

    @staticmethod
    def record_analysis(exercise_type: str, duration: float, risk_level: str):
        """Record exercise analysis metrics"""
        analysis_requests_total.labels(exercise_type=exercise_type).inc()
        analysis_duration.labels(exercise_type=exercise_type).observe(duration)
        risk_levels.labels(level=risk_level).inc()

    @staticmethod
    def record_ai_feedback(status: str, duration: float):
        """Record AI feedback generation metrics"""
        ai_feedback_total.labels(status=status).inc()
        if status != "success":
            ai_fallback_events.labels(reason=status).inc()

    @staticmethod
    def record_cache_hit(cache_type: str):
        """Record cache hit"""
        cache_hits.labels(cache_type=cache_type).inc()

    @staticmethod
    def record_cache_miss(cache_type: str):
        """Record cache miss"""
        cache_misses.labels(cache_type=cache_type).inc()

    @staticmethod
    def record_db_operation(table: str, operation: str, duration: float, success: bool):
        """Record database operation metrics"""
        status = "success" if success else "failed"
        db_operations.labels(operation=operation, table=table, status=status).inc()
        db_query_duration.labels(table=table, operation=operation).observe(duration)

    @staticmethod
    def record_error(error_type: str, endpoint: str = "unknown"):
        """Record error metrics"""
        errors_total.labels(error_type=error_type, endpoint=endpoint).inc()

    @staticmethod
    def record_background_task(operation: str, status: str):
        """Record background task metrics"""
        background_tasks_completed.labels(operation=operation, status=status).inc()

    @staticmethod
    def record_rate_limit(endpoint: str):
        """Record rate limit violation"""
        rate_limit_hits.labels(endpoint=endpoint).inc()

    @staticmethod
    def record_gemini_call(status: str, duration: float):
        """Record Gemini API call metrics"""
        gemini_api_calls.labels(status=status).inc()
        gemini_api_duration.observe(duration)

    @staticmethod
    def update_active_requests(count: int):
        """Update active request gauge"""
        active_requests.set(count)

    @staticmethod
    def update_active_background_tasks(count: int):
        """Update active background tasks gauge"""
        active_background_tasks.set(count)


# Initialize app info
app_info.info(
    {
        "version": "2.0.0-phase2",
        "environment": "production",
        "features": "security,performance,monitoring",
    }
)

logger.info("✅ Prometheus metrics initialized")
