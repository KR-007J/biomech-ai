"""
Tier 2: Time-Series Analytics Engine
======================================

Advanced temporal analysis for biomechanical data:
- Trend detection and forecasting
- Anomaly detection (Isolation Forest, LOF)
- Correlation analysis
- Movement pattern hashing
- Comparative analytics (peer benchmarking)
"""

import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
import json

logger = logging.getLogger(__name__)


class TrendDirection(Enum):
    """Trend classification"""

    IMPROVING = "improving"
    STABLE = "stable"
    DEGRADING = "degrading"
    CRITICAL = "critical"


@dataclass
class TimeSeriesPoint:
    """Single data point in time series"""

    timestamp: datetime
    value: float
    confidence: float = 1.0
    metadata: Dict[str, Any] = None


@dataclass
class Anomaly:
    """Detected anomaly in time series"""

    timestamp: datetime
    value: float
    expected_value: float
    deviation_score: float  # Standard deviations from mean
    severity: str  # "low", "medium", "high", "critical"
    explanation: str


@dataclass
class TrendAnalysis:
    """Trend analysis result"""

    metric_name: str
    trend_direction: TrendDirection
    trend_slope: float  # Rate of change
    r_squared: float  # Fit quality
    forecast_7_days: List[float]
    confidence: float
    last_updated: datetime


@dataclass
class CorrelationPair:
    """Correlation between two metrics"""

    metric_1: str
    metric_2: str
    correlation_coefficient: float  # -1 to 1
    p_value: float
    significance: str  # "not_significant", "significant", "highly_significant"


class TimeSeriesAnalyzer:
    """Analyze biomechanical time series data"""

    def __init__(self, window_size: int = 30):
        """
        Initialize analyzer

        Args:
            window_size: Number of data points for analysis
        """
        self.window_size = window_size
        self.data_history: Dict[str, List[TimeSeriesPoint]] = {}
        self.anomalies: Dict[str, List[Anomaly]] = {}

    def add_datapoint(
        self,
        metric_name: str,
        value: float,
        timestamp: Optional[datetime] = None,
        confidence: float = 1.0,
    ) -> None:
        """Add single data point"""
        if metric_name not in self.data_history:
            self.data_history[metric_name] = []

        self.data_history[metric_name].append(
            TimeSeriesPoint(
                timestamp=timestamp or datetime.utcnow(), value=value, confidence=confidence
            )
        )

        # Keep only recent data
        if len(self.data_history[metric_name]) > self.window_size * 2:
            self.data_history[metric_name] = self.data_history[metric_name][-self.window_size :]

    def get_trend(self, metric_name: str, window: Optional[int] = None) -> Optional[TrendAnalysis]:
        """
        Analyze trend for metric

        Args:
            metric_name: Metric to analyze
            window: Analysis window (default: full history)

        Returns:
            Trend analysis result
        """
        if metric_name not in self.data_history:
            return None

        points = self.data_history[metric_name]
        if len(points) < 3:
            return None

        window = window or len(points)
        recent_points = points[-window:]

        try:
            # Extract values and timestamps
            values = np.array([p.value for p in recent_points])
            x = np.arange(len(values))

            # Linear regression
            coeffs = np.polyfit(x, values, 1)
            slope = coeffs[0]
            intercept = coeffs[1]

            # Fit quality
            y_pred = np.polyval(coeffs, x)
            ss_res = np.sum((values - y_pred) ** 2)
            ss_tot = np.sum((values - np.mean(values)) ** 2)
            r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0

            # Determine trend direction
            if abs(slope) < 0.01:
                direction = TrendDirection.STABLE
                confidence = 0.7
            elif slope > 0.05:
                direction = TrendDirection.DEGRADING
                confidence = 0.85
            elif slope < -0.05:
                direction = TrendDirection.IMPROVING
                confidence = 0.85
            else:
                direction = TrendDirection.STABLE
                confidence = 0.6

            # 7-day forecast
            future_x = np.arange(len(values), len(values) + 7)
            forecast = np.polyval(coeffs, future_x).tolist()

            return TrendAnalysis(
                metric_name=metric_name,
                trend_direction=direction,
                trend_slope=float(slope),
                r_squared=float(r_squared),
                forecast_7_days=forecast,
                confidence=float(confidence),
                last_updated=datetime.utcnow(),
            )
        except Exception as e:
            logger.error(f"Trend analysis error for {metric_name}: {e}")
            return None

    def detect_anomalies(
        self, metric_name: str, method: str = "isolation_forest", threshold: float = 2.5
    ) -> List[Anomaly]:
        """
        Detect anomalies in time series

        Args:
            metric_name: Metric to analyze
            method: "isolation_forest", "lof", or "zscore"
            threshold: Sensitivity threshold

        Returns:
            List of detected anomalies
        """
        if metric_name not in self.data_history:
            return []

        points = self.data_history[metric_name]
        if len(points) < 5:
            return []

        values = np.array([p.value for p in points]).reshape(-1, 1)

        try:
            anomalies = []

            if method == "zscore":
                # Z-score anomaly detection
                mean = np.mean(values)
                std = np.std(values)

                for i, (point, value) in enumerate(zip(points, values)):
                    z_score = abs((value[0] - mean) / (std + 1e-6))
                    if z_score > threshold:
                        expected = mean
                        severity = (
                            "critical" if z_score > 4 else "high" if z_score > 3 else "medium"
                        )
                        anomalies.append(
                            Anomaly(
                                timestamp=point.timestamp,
                                value=float(value[0]),
                                expected_value=float(expected),
                                deviation_score=float(z_score),
                                severity=severity,
                                explanation=f"Value {value[0]:.2f} deviates {z_score:.2f}σ from mean",
                            )
                        )

            elif method == "isolation_forest":
                try:
                    from sklearn.ensemble import IsolationForest

                    iso_forest = IsolationForest(contamination=0.1, random_state=42)
                    predictions = iso_forest.fit_predict(values)

                    mean = np.mean(values)
                    for i, (pred, point, value) in enumerate(zip(predictions, points, values)):
                        if pred == -1:  # Anomaly
                            deviation = abs((value[0] - mean) / (np.std(values) + 1e-6))
                            severity = (
                                "critical"
                                if deviation > 4
                                else "high" if deviation > 2.5 else "medium"
                            )
                            anomalies.append(
                                Anomaly(
                                    timestamp=point.timestamp,
                                    value=float(value[0]),
                                    expected_value=float(mean),
                                    deviation_score=float(deviation),
                                    severity=severity,
                                    explanation=f"Anomalous pattern detected by Isolation Forest",
                                )
                            )
                except ImportError:
                    logger.warning("scikit-learn not installed, falling back to zscore")
                    return self.detect_anomalies(metric_name, "zscore", threshold)

            elif method == "lof":
                try:
                    from sklearn.neighbors import LocalOutlierFactor

                    lof = LocalOutlierFactor(n_neighbors=5)
                    predictions = lof.fit_predict(values)

                    mean = np.mean(values)
                    for i, (pred, point, value) in enumerate(zip(predictions, points, values)):
                        if pred == -1:  # Anomaly
                            deviation = abs((value[0] - mean) / (np.std(values) + 1e-6))
                            severity = (
                                "critical"
                                if deviation > 4
                                else "high" if deviation > 2.5 else "medium"
                            )
                            anomalies.append(
                                Anomaly(
                                    timestamp=point.timestamp,
                                    value=float(value[0]),
                                    expected_value=float(mean),
                                    deviation_score=float(deviation),
                                    severity=severity,
                                    explanation=f"Local outlier detected",
                                )
                            )
                except ImportError:
                    logger.warning("scikit-learn not installed, falling back to zscore")
                    return self.detect_anomalies(metric_name, "zscore", threshold)

            # Cache anomalies
            if metric_name not in self.anomalies:
                self.anomalies[metric_name] = []
            self.anomalies[metric_name].extend(anomalies)

            return anomalies
        except Exception as e:
            logger.error(f"Anomaly detection error: {e}")
            return []

    def get_correlation(self, metric_1: str, metric_2: str) -> Optional[CorrelationPair]:
        """
        Calculate correlation between two metrics

        Args:
            metric_1: First metric name
            metric_2: Second metric name

        Returns:
            Correlation pair with statistics
        """
        if metric_1 not in self.data_history or metric_2 not in self.data_history:
            return None

        points_1 = self.data_history[metric_1]
        points_2 = self.data_history[metric_2]

        if len(points_1) < 2 or len(points_2) < 2:
            return None

        try:
            from scipy import stats

            # Align data by timestamp
            values_1 = np.array([p.value for p in points_1])
            values_2 = np.array([p.value for p in points_2])

            # Truncate to same length
            min_len = min(len(values_1), len(values_2))
            values_1 = values_1[-min_len:]
            values_2 = values_2[-min_len:]

            # Pearson correlation
            corr_coeff, p_value = stats.pearsonr(values_1, values_2)

            # Significance
            if p_value < 0.001:
                significance = "highly_significant"
            elif p_value < 0.05:
                significance = "significant"
            else:
                significance = "not_significant"

            return CorrelationPair(
                metric_1=metric_1,
                metric_2=metric_2,
                correlation_coefficient=float(corr_coeff),
                p_value=float(p_value),
                significance=significance,
            )
        except Exception as e:
            logger.error(f"Correlation error: {e}")
            return None

    def get_summary_stats(self, metric_name: str) -> Dict[str, float]:
        """Get summary statistics for metric"""
        if metric_name not in self.data_history:
            return {}

        values = np.array([p.value for p in self.data_history[metric_name]])

        return {
            "count": float(len(values)),
            "mean": float(np.mean(values)),
            "std": float(np.std(values)),
            "min": float(np.min(values)),
            "max": float(np.max(values)),
            "median": float(np.median(values)),
            "q25": float(np.percentile(values, 25)),
            "q75": float(np.percentile(values, 75)),
            "skewness": float((np.mean(values) - np.median(values)) / (np.std(values) + 1e-6)),
        }


class ComparativeAnalyticsEngine:
    """Compare user performance to benchmarks and cohorts"""

    def __init__(self):
        self.user_benchmarks: Dict[str, Dict[str, float]] = {}
        self.cohort_data: Dict[str, Dict[str, List[float]]] = {}

    def add_user_data(self, user_id: str, metrics: Dict[str, float]) -> None:
        """Add user performance metrics"""
        if user_id not in self.user_benchmarks:
            self.user_benchmarks[user_id] = {}
        self.user_benchmarks[user_id].update(metrics)

    def add_cohort_data(self, cohort_name: str, metric_name: str, values: List[float]) -> None:
        """Add cohort benchmark data"""
        if cohort_name not in self.cohort_data:
            self.cohort_data[cohort_name] = {}
        if metric_name not in self.cohort_data[cohort_name]:
            self.cohort_data[cohort_name][metric_name] = []

        self.cohort_data[cohort_name][metric_name].extend(values)

    def get_percentile_ranking(
        self, user_id: str, metric_name: str, cohort_name: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get user's percentile ranking in cohort

        Args:
            user_id: User ID
            metric_name: Metric to compare
            cohort_name: Cohort to compare against

        Returns:
            Percentile ranking and statistics
        """
        if (
            user_id not in self.user_benchmarks
            or cohort_name not in self.cohort_data
            or metric_name not in self.cohort_data[cohort_name]
        ):
            return None

        user_value = self.user_benchmarks[user_id].get(metric_name)
        cohort_values = self.cohort_data[cohort_name][metric_name]

        if user_value is None or len(cohort_values) == 0:
            return None

        # Calculate percentile
        percentile = (np.sum(np.array(cohort_values) <= user_value) / len(cohort_values)) * 100

        return {
            "user_value": float(user_value),
            "cohort_mean": float(np.mean(cohort_values)),
            "cohort_std": float(np.std(cohort_values)),
            "percentile": float(percentile),
            "rank": (
                f"Top {100 - percentile:.0f}%" if percentile > 50 else f"Bottom {percentile:.0f}%"
            ),
            "z_score": float(
                (user_value - np.mean(cohort_values)) / (np.std(cohort_values) + 1e-6)
            ),
        }

    def get_peer_comparison(
        self, user_id: str, similar_users: List[str], metrics: List[str]
    ) -> Dict[str, Any]:
        """Compare user to similar peers"""
        comparison = {"user_id": user_id, "similar_users": similar_users, "metrics": {}}

        for metric in metrics:
            user_val = self.user_benchmarks.get(user_id, {}).get(metric)
            peer_vals = [self.user_benchmarks.get(uid, {}).get(metric) for uid in similar_users]
            peer_vals = [v for v in peer_vals if v is not None]

            if user_val is not None and peer_vals:
                comparison["metrics"][metric] = {
                    "user_value": float(user_val),
                    "peer_mean": float(np.mean(peer_vals)),
                    "peer_std": float(np.std(peer_vals)),
                    "better_than_peers": user_val
                    < np.mean(peer_vals),  # Assuming lower is better for most metrics
                    "difference": float(user_val - np.mean(peer_vals)),
                }

        return comparison


class MovementSignatureGenerator:
    """Generate and analyze unique movement signatures"""

    @staticmethod
    def generate_signature(
        joint_angles: Dict[str, float], movement_metrics: Dict[str, float]
    ) -> str:
        """
        Generate movement signature hash

        Args:
            joint_angles: Dictionary of joint angles
            movement_metrics: Additional metrics (smoothness, speed, etc.)

        Returns:
            Hex signature string
        """
        import hashlib

        # Quantize angles to reduce noise
        quantized = {}
        for joint, angle in joint_angles.items():
            quantized[joint] = round(angle / 5) * 5  # 5-degree bins

        # Create canonical string
        sig_str = json.dumps(quantized, sort_keys=True) + json.dumps(
            movement_metrics, sort_keys=True
        )

        # Hash
        return hashlib.md5(sig_str.encode()).hexdigest()

    @staticmethod
    def detect_new_patterns(
        historical_signatures: List[str], new_signature: str, similarity_threshold: float = 0.95
    ) -> bool:
        """
        Detect if new movement is novel

        Args:
            historical_signatures: Previous signatures
            new_signature: New signature to check
            similarity_threshold: Minimum similarity to match

        Returns:
            True if pattern is novel
        """
        # Simple approach: check for exact match
        if new_signature in historical_signatures:
            return False

        return True


if __name__ == "__main__":
    # Example usage
    analyzer = TimeSeriesAnalyzer(window_size=30)

    # Add sample data
    for i in range(30):
        analyzer.add_datapoint("knee_angle", 45 + i * 0.5 + np.random.normal(0, 2))
        analyzer.add_datapoint("risk_score", 30 + i * 0.2 + np.random.normal(0, 3))

    # Get trend
    trend = analyzer.get_trend("knee_angle")
    print(f"Trend: {trend.trend_direction.value} (slope: {trend.trend_slope:.4f})")

    # Detect anomalies
    anomalies = analyzer.detect_anomalies("risk_score", method="zscore")
    print(f"Anomalies: {len(anomalies)}")

    # Get correlation
    corr = analyzer.get_correlation("knee_angle", "risk_score")
    if corr:
        print(f"Correlation: {corr.correlation_coefficient:.3f}")
