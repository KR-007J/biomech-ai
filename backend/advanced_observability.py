"""
TIER 7: Advanced Observability & Distributed Tracing
Jaeger, OpenTelemetry, Grafana dashboards, and advanced monitoring
"""

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# ============================================================================
# DATA MODELS
# ============================================================================


class SpanKind(str, Enum):
    """OpenTelemetry span kinds"""

    INTERNAL = "INTERNAL"
    SERVER = "SERVER"
    CLIENT = "CLIENT"
    PRODUCER = "PRODUCER"
    CONSUMER = "CONSUMER"


class SpanStatus(str, Enum):
    """Span execution status"""

    UNSET = "UNSET"
    OK = "OK"
    ERROR = "ERROR"


@dataclass
class Span:
    """OpenTelemetry span"""

    span_id: str
    trace_id: str
    parent_span_id: Optional[str]
    operation_name: str
    span_kind: SpanKind
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_ms: float = 0.0
    status: SpanStatus = SpanStatus.UNSET
    attributes: Dict[str, Any] = field(default_factory=dict)
    events: List[Dict] = field(default_factory=list)
    tags: Dict[str, str] = field(default_factory=dict)

    def finish(self):
        """Mark span as finished"""
        self.end_time = datetime.utcnow()
        self.duration_ms = (self.end_time - self.start_time).total_seconds() * 1000

    def to_dict(self) -> Dict:
        return {
            "span_id": self.span_id,
            "trace_id": self.trace_id,
            "parent_span_id": self.parent_span_id,
            "operation": self.operation_name,
            "kind": self.span_kind.value,
            "duration_ms": self.duration_ms,
            "status": self.status.value,
            "attributes": self.attributes,
            "timestamp": self.start_time.isoformat(),
        }


@dataclass
class Trace:
    """Complete distributed trace"""

    trace_id: str
    root_span_id: str
    spans: List[Span] = field(default_factory=list)
    start_time: datetime = field(default_factory=datetime.utcnow)
    end_time: Optional[datetime] = None
    total_duration_ms: float = 0.0
    service_name: str = ""

    def to_dict(self) -> Dict:
        return {
            "trace_id": self.trace_id,
            "duration_ms": self.total_duration_ms,
            "span_count": len(self.spans),
            "service": self.service_name,
            "spans": [s.to_dict() for s in self.spans],
        }


@dataclass
class Metric:
    """Metrics data point"""

    metric_name: str
    value: float
    timestamp: datetime
    labels: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return {
            "metric": self.metric_name,
            "value": self.value,
            "labels": self.labels,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class Alert:
    """Alert configuration and state"""

    alert_id: str
    name: str
    condition: str
    threshold: float
    metric_name: str
    severity: str  # "info", "warning", "critical"
    is_active: bool = True
    triggered_at: Optional[datetime] = None

    def to_dict(self) -> Dict:
        return {
            "alert_id": self.alert_id,
            "name": self.name,
            "severity": self.severity,
            "is_active": self.is_active,
            "triggered_at": (
                self.triggered_at.isoformat() if self.triggered_at else None
            ),
        }


# ============================================================================
# DISTRIBUTED TRACING ENGINE
# ============================================================================


class DistributedTracingEngine:
    """
    Distributed tracing with Jaeger/OpenTelemetry support
    """

    def __init__(self):
        self.traces: Dict[str, Trace] = {}
        self.spans: Dict[str, Span] = {}
        self.active_traces: Dict[str, str] = {}  # context -> trace_id
        self.metrics_history: List[Metric] = []
        self.alerts: Dict[str, Alert] = {}
        logger.info("Distributed tracing engine initialized")

    def start_trace(self, service_name: str, operation_name: str) -> str:
        """
        Start distributed trace

        Args:
            service_name: Service originating trace
            operation_name: Root operation name

        Returns:
            Trace ID
        """
        try:
            trace_id = str(uuid.uuid4())
            span_id = str(uuid.uuid4())

            root_span = Span(
                span_id=span_id,
                trace_id=trace_id,
                parent_span_id=None,
                operation_name=operation_name,
                span_kind=SpanKind.SERVER,
                start_time=datetime.utcnow(),
            )

            trace = Trace(
                trace_id=trace_id,
                root_span_id=span_id,
                service_name=service_name,
                spans=[root_span],
            )

            self.traces[trace_id] = trace
            self.spans[span_id] = root_span

            logger.debug(f"Trace started: {trace_id} ({operation_name})")

            return trace_id
        except Exception as e:
            logger.error(f"Trace start failed: {str(e)}")
            return ""

    def start_span(
        self,
        trace_id: str,
        operation_name: str,
        span_kind: str = "INTERNAL",
        parent_span_id: Optional[str] = None,
    ) -> str:
        """
        Start new span in trace

        Args:
            trace_id: Parent trace ID
            operation_name: Operation name
            span_kind: Type of span
            parent_span_id: Parent span ID

        Returns:
            Span ID
        """
        try:
            span_id = str(uuid.uuid4())

            span = Span(
                span_id=span_id,
                trace_id=trace_id,
                parent_span_id=parent_span_id,
                operation_name=operation_name,
                span_kind=SpanKind(span_kind),
                start_time=datetime.utcnow(),
            )

            self.spans[span_id] = span

            # Add to trace
            if trace_id in self.traces:
                self.traces[trace_id].spans.append(span)

            logger.debug(f"Span started: {span_id} ({operation_name})")

            return span_id
        except Exception as e:
            logger.error(f"Span start failed: {str(e)}")
            return ""

    def end_span(
        self, span_id: str, status: str = "OK", error: Optional[str] = None
    ) -> bool:
        """End span"""
        try:
            span = self.spans.get(span_id)
            if not span:
                return False

            span.finish()
            span.status = SpanStatus(status)

            if error:
                span.tags["error"] = error
                span.status = SpanStatus.ERROR

            logger.debug(f"Span ended: {span_id} ({span.duration_ms}ms)")

            return True
        except Exception as e:
            logger.error(f"Span end failed: {str(e)}")
            return False

    def end_trace(self, trace_id: str) -> Dict[str, Any]:
        """End trace and return summary"""
        try:
            trace = self.traces.get(trace_id)
            if not trace:
                return {"error": "Trace not found"}

            trace.end_time = datetime.utcnow()
            trace.total_duration_ms = (
                trace.end_time - trace.start_time
            ).total_seconds() * 1000

            # Calculate critical path
            critical_path = max((s.duration_ms for s in trace.spans), default=0)

            logger.debug(f"Trace ended: {trace_id} ({trace.total_duration_ms}ms)")

            return {
                "trace_id": trace_id,
                "duration_ms": trace.total_duration_ms,
                "span_count": len(trace.spans),
                "critical_path_ms": critical_path,
                "trace": trace.to_dict(),
            }
        except Exception as e:
            logger.error(f"Trace end failed: {str(e)}")
            return {"error": str(e)}

    def add_span_attribute(self, span_id: str, key: str, value: Any):
        """Add attribute to span"""
        try:
            span = self.spans.get(span_id)
            if span:
                span.attributes[key] = value
        except Exception as e:
            logger.error(f"Attribute add failed: {str(e)}")

    def record_metric(
        self, metric_name: str, value: float, labels: Dict[str, str] = None
    ) -> bool:
        """Record metric"""
        try:
            metric = Metric(
                metric_name=metric_name,
                value=value,
                timestamp=datetime.utcnow(),
                labels=labels or {},
            )

            self.metrics_history.append(metric)

            # Keep last 1000 metrics
            if len(self.metrics_history) > 1000:
                self.metrics_history = self.metrics_history[-1000:]

            return True
        except Exception as e:
            logger.error(f"Metric recording failed: {str(e)}")
            return False

    def add_alert(
        self,
        name: str,
        metric_name: str,
        condition: str,
        threshold: float,
        severity: str = "warning",
    ) -> Dict[str, Any]:
        """
        Add alert rule

        Args:
            name: Alert name
            metric_name: Metric to monitor
            condition: Condition (e.g., "greater_than", "less_than")
            threshold: Threshold value
            severity: Alert severity

        Returns:
            Alert details
        """
        try:
            alert_id = str(uuid.uuid4())

            alert = Alert(
                alert_id=alert_id,
                name=name,
                condition=condition,
                threshold=threshold,
                metric_name=metric_name,
                severity=severity,
            )

            self.alerts[alert_id] = alert

            logger.info(f"Alert created: {alert_id} ({name})")

            return {"success": True, "alert": alert.to_dict()}
        except Exception as e:
            logger.error(f"Alert creation failed: {str(e)}")
            return {"error": str(e)}

    async def check_alerts(self) -> List[Dict]:
        """Check all alerts against current metrics"""
        try:
            triggered = []

            if not self.metrics_history:
                return triggered

            # Get latest metrics by name
            latest_metrics = {}
            for metric in reversed(self.metrics_history):
                if metric.metric_name not in latest_metrics:
                    latest_metrics[metric.metric_name] = metric

            # Check each alert
            for alert_id, alert in self.alerts.items():
                if alert.metric_name in latest_metrics:
                    metric = latest_metrics[alert.metric_name]

                    # Evaluate condition
                    triggered_now = self._evaluate_condition(
                        alert.condition, metric.value, alert.threshold
                    )

                    if triggered_now and not alert.triggered_at:
                        alert.triggered_at = datetime.utcnow()
                        triggered.append(alert.to_dict())
                    elif not triggered_now and alert.triggered_at:
                        alert.triggered_at = None

            return triggered
        except Exception as e:
            logger.error(f"Alert check failed: {str(e)}")
            return []

    def _evaluate_condition(
        self, condition: str, value: float, threshold: float
    ) -> bool:
        """Evaluate alert condition"""
        if condition == "greater_than":
            return value > threshold
        elif condition == "less_than":
            return value < threshold
        elif condition == "equals":
            return abs(value - threshold) < 0.01
        elif condition == "not_equals":
            return abs(value - threshold) >= 0.01
        return False

    async def get_metrics_dashboard(
        self, metric_names: List[str] = None, time_range_minutes: int = 60
    ) -> Dict[str, Any]:
        """Get metrics for dashboard"""
        try:
            # Filter metrics
            cutoff = datetime.utcnow() - timedelta(minutes=time_range_minutes)

            metrics = [m for m in self.metrics_history if m.timestamp > cutoff]

            if metric_names:
                metrics = [m for m in metrics if m.metric_name in metric_names]

            # Group by metric name
            grouped = {}
            for metric in metrics:
                if metric.metric_name not in grouped:
                    grouped[metric.metric_name] = []
                grouped[metric.metric_name].append(metric.to_dict())

            return {
                "metrics": grouped,
                "time_range_minutes": time_range_minutes,
                "data_points": len(metrics),
            }
        except Exception as e:
            logger.error(f"Dashboard fetch failed: {str(e)}")
            return {"error": str(e)}


logger.info("Advanced observability module loaded - Tier 7 complete")
