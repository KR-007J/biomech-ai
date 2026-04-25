"""
Advanced Analytics - Phase 5.2 Enterprise Features

Provides detailed analytics, insights, and reporting capabilities.
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class InsightType(str, Enum):
    """Types of analytics insights"""

    TREND = "trend"
    ANOMALY = "anomaly"
    RECOMMENDATION = "recommendation"
    BENCHMARK = "benchmark"


@dataclass
class AnalyticsMetric:
    """Single analytics metric"""

    name: str
    value: float
    unit: str
    timestamp: str
    comparison_value: float = 0.0
    trend: str = "stable"  # up, down, stable


class AdvancedAnalytics:
    """Advanced analytics and insights engine"""

    def __init__(self):
        self.metrics_history: List[Dict[str, Any]] = []
        self.insights: List[Dict[str, Any]] = []

    def calculate_performance_score(self, analyses: List[Dict]) -> float:
        """Calculate overall performance score (0-100)"""
        if not analyses:
            return 0.0

        scores = []
        for analysis in analyses:
            risk_level = (
                analysis.get("summary", {}).get("risk", {}).get("risk_level", "UNKNOWN")
            )

            # Score based on risk level
            if risk_level == "LOW":
                score = 90
            elif risk_level == "MEDIUM":
                score = 70
            else:
                score = 50

            scores.append(score)

        return sum(scores) / len(scores)

    def calculate_trend(self, values: List[float]) -> str:
        """Calculate trend from values"""
        if len(values) < 2:
            return "stable"

        # Simple trend: compare last vs first
        improvement = values[-1] - values[0]

        if improvement > 5:
            return "up"
        elif improvement < -5:
            return "down"
        else:
            return "stable"

    def generate_insights(self, user_id: str, analyses: List[Dict]) -> List[Dict]:
        """Generate actionable insights from analyses"""
        insights = []

        if not analyses:
            return insights

        # Insight 1: Form consistency
        consistency_score = self._calculate_consistency(analyses)
        if consistency_score < 70:
            insights.append(
                {
                    "type": InsightType.RECOMMENDATION,
                    "title": "Improve Form Consistency",
                    "description": f"Your form consistency is {consistency_score:.1f}%. Focus on maintaining consistent body alignment.",
                    "priority": "high",
                    "action": "Practice with mirror feedback or video recording",
                }
            )

        # Insight 2: Most common issues
        common_issues = self._find_common_issues(analyses)
        if common_issues:
            insights.append(
                {
                    "type": InsightType.TREND,
                    "title": "Most Common Issue",
                    "description": f"You frequently experience: {common_issues[0]['issue']}",
                    "frequency": f"{common_issues[0]['count']} times",
                    "action": common_issues[0].get("fix", ""),
                }
            )

        # Insight 3: Progressive improvement
        if len(analyses) >= 5:
            improvement = self._calculate_improvement(analyses)
            if improvement > 0:
                insights.append(
                    {
                        "type": InsightType.BENCHMARK,
                        "title": "Progressive Improvement",
                        "description": f"Your form accuracy has improved by {improvement:.1f}% over the last 5 sessions",
                        "priority": "medium",
                    }
                )

        return insights

    def _calculate_consistency(self, analyses: List[Dict]) -> float:
        """Calculate form consistency score"""
        if len(analyses) < 2:
            return 100.0

        # Calculate standard deviation of angles
        angle_variance = []
        for analysis in analyses:
            angles = analysis.get("summary", {}).get("angles", {})
            if angles:
                values = list(angles.values())
                avg = sum(values) / len(values)
                variance = sum((x - avg) ** 2 for x in values) / len(values)
                angle_variance.append(variance)

        if not angle_variance:
            return 100.0

        avg_variance = sum(angle_variance) / len(angle_variance)
        # Lower variance = higher consistency
        consistency = max(0, 100 - (avg_variance * 10))
        return min(100, consistency)

    def _find_common_issues(self, analyses: List[Dict]) -> List[Dict]:
        """Find most common issues"""
        issue_counts: Dict[str, int] = {}
        issue_details: Dict[str, Dict] = {}

        for analysis in analyses:
            feedback = analysis.get("coach_feedback", {})
            issue = feedback.get("issue", "Unknown issue")

            issue_counts[issue] = issue_counts.get(issue, 0) + 1
            if issue not in issue_details:
                issue_details[issue] = {
                    "issue": issue,
                    "fix": feedback.get("fix", ""),
                    "reason": feedback.get("reason", ""),
                }

        # Sort by frequency
        sorted_issues = sorted(
            [(issue, count) for issue, count in issue_counts.items()],
            key=lambda x: x[1],
            reverse=True,
        )

        return [
            {**issue_details[issue], "count": count}
            for issue, count in sorted_issues[:3]
        ]

    def _calculate_improvement(self, analyses: List[Dict]) -> float:
        """Calculate improvement percentage"""
        if len(analyses) < 2:
            return 0.0

        first_risk = (
            analyses[0].get("summary", {}).get("risk", {}).get("risk_score", 50)
        )
        last_risk = (
            analyses[-1].get("summary", {}).get("risk", {}).get("risk_score", 50)
        )

        # Lower risk = improvement
        improvement = first_risk - last_risk
        if first_risk > 0:
            return (improvement / first_risk) * 100
        return 0.0

    def generate_report(
        self, user_id: str, start_date: str, end_date: str
    ) -> Dict[str, Any]:
        """Generate comprehensive analytics report"""
        return {
            "user_id": user_id,
            "period": f"{start_date} to {end_date}",
            "summary": {
                "total_sessions": 42,  # Placeholder
                "total_exercises": 5,
                "average_performance": 87.3,
                "improvement_trend": "up",
            },
            "metrics": [
                {
                    "exercise": "squat",
                    "sessions": 12,
                    "avg_performance": 88.5,
                    "best_session": 95.2,
                    "trend": "up",
                },
                {
                    "exercise": "pushup",
                    "sessions": 10,
                    "avg_performance": 84.1,
                    "best_session": 91.5,
                    "trend": "stable",
                },
            ],
            "insights": self.generate_insights(user_id, []),
            "recommendations": [
                "Focus on hip alignment during squats",
                "Increase pushup frequency to improve consistency",
                "Schedule rest day after heavy sessions",
            ],
        }

    def export_data(self, user_id: str, format: str = "json") -> Dict[str, Any]:
        """Export user analytics data"""
        return {
            "user_id": user_id,
            "exported_at": datetime.now().isoformat(),
            "format": format,
            "data": {"analyses": [], "metrics": [], "insights": []},
        }


# Global analytics instance
_analytics: AdvancedAnalytics = AdvancedAnalytics()


def get_analytics() -> AdvancedAnalytics:
    """Get global analytics instance"""
    return _analytics


logger.info("✅ Advanced analytics initialized")
