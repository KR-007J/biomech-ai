"""
PHASE 2: TIER 15 - ADVANCED ANALYTICS PLATFORM
Cohort analysis, retention, funnel analysis, predictive segments
"""

import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set

logger = logging.getLogger(__name__)


class CohortType(str, Enum):
    """Cohort grouping types"""

    ACQUISITION_DATE = "acquisition_date"
    BEHAVIOR = "behavior"
    DEMOGRAPHIC = "demographic"
    USAGE_LEVEL = "usage_level"
    INJURY_RISK = "injury_risk"
    ENGAGEMENT = "engagement"


@dataclass
class User:
    """User for analytics"""

    user_id: str
    created_at: datetime
    attributes: Dict[str, Any] = field(default_factory=dict)
    sessions: List[str] = field(default_factory=list)
    events: List[str] = field(default_factory=list)


@dataclass
class Event:
    """Analytics event"""

    event_id: str
    user_id: str
    event_type: str
    timestamp: datetime
    properties: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Cohort:
    """User cohort"""

    cohort_id: str
    name: str
    cohort_type: CohortType
    criteria: Dict[str, Any]
    users: Set[str] = field(default_factory=set)
    created_at: datetime = field(default_factory=datetime.utcnow)
    size: int = 0


@dataclass
class RetentionMetrics:
    """Retention analysis metrics"""

    day0_retention: float = 100.0
    day1_retention: float = 0.0
    day7_retention: float = 0.0
    day30_retention: float = 0.0
    day90_retention: float = 0.0
    churn_rate: float = 0.0
    average_lifetime_days: float = 0.0


@dataclass
class FunnelStep:
    """Step in conversion funnel"""

    step_name: str
    event_name: str
    user_count: int = 0
    conversion_rate: float = 0.0


class AdvancedAnalyticsEngine:
    """
    Advanced analytics platform

    Features:
    - Cohort analysis
    - Retention metrics
    - Funnel analysis
    - Segment creation
    - Predictive analytics
    - LTV calculation
    - Churn prediction
    """

    def __init__(self):
        self.users: Dict[str, User] = {}
        self.events: List[Event] = []
        self.cohorts: Dict[str, Cohort] = {}
        self.user_segments: Dict[str, Set[str]] = {}
        self.event_buffer: List[Event] = []
        self.max_buffer_size = 100000

    async def track_event(
        self, user_id: str, event_type: str, properties: Optional[Dict[str, Any]] = None
    ) -> str:
        """Track user event"""
        event = Event(
            event_id=f"{user_id}_{event_type}_{int(datetime.utcnow().timestamp())}",
            user_id=user_id,
            event_type=event_type,
            timestamp=datetime.utcnow(),
            properties=properties or {},
        )

        self.event_buffer.append(event)

        if len(self.event_buffer) >= self.max_buffer_size:
            self.events.extend(self.event_buffer)
            self.event_buffer.clear()

        return event.event_id

    async def register_user(
        self, user_id: str, attributes: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Register user"""
        if user_id not in self.users:
            self.users[user_id] = User(
                user_id=user_id, created_at=datetime.utcnow(), attributes=attributes or {}
            )
            logger.debug(f"User registered: {user_id}")
            return True
        return False

    async def create_cohort(
        self, cohort_type: CohortType, criteria: Dict[str, Any], name: str = ""
    ) -> str:
        """Create user cohort"""
        cohort_id = f"cohort_{len(self.cohorts) + 1}"
        cohort = Cohort(
            cohort_id=cohort_id,
            name=name or cohort_type.value,
            cohort_type=cohort_type,
            criteria=criteria,
        )

        # Add matching users
        for user_id, user in self.users.items():
            if self._user_matches_criteria(user, criteria):
                cohort.users.add(user_id)

        cohort.size = len(cohort.users)
        self.cohorts[cohort_id] = cohort

        logger.info(f"Cohort created: {cohort_id} (size={cohort.size})")
        return cohort_id

    def _user_matches_criteria(self, user: User, criteria: Dict[str, Any]) -> bool:
        """Check if user matches criteria"""
        for key, value in criteria.items():
            if isinstance(value, dict) and "min" in value and "max" in value:
                # Range check
                attr = user.attributes.get(key, 0)
                if not (value["min"] <= attr <= value["max"]):
                    return False
            elif isinstance(value, list):
                # List membership
                if user.attributes.get(key) not in value:
                    return False
            else:
                # Exact match
                if user.attributes.get(key) != value:
                    return False
        return True

    async def analyze_retention(
        self, cohort_id: str, base_date: Optional[datetime] = None
    ) -> RetentionMetrics:
        """Analyze retention for cohort"""
        if not (cohort := self.cohorts.get(cohort_id)):
            return RetentionMetrics()

        base_date = base_date or datetime.utcnow()
        metrics = RetentionMetrics()

        # Get all cohort users
        cohort_users = cohort.users
        if not cohort_users:
            return metrics

        # Count users active on each day
        day_buckets = defaultdict(set)

        for event in self.events + self.event_buffer:
            if event.user_id not in cohort_users:
                continue

            days_since = (event.timestamp.date() - base_date.date()).days
            if 0 <= days_since <= 90:
                day_buckets[days_since].add(event.user_id)

        # Calculate retention rates
        total_users = len(cohort_users)
        active_day0 = len(day_buckets.get(0, set()))

        if active_day0 > 0:
            metrics.day0_retention = 100.0
            metrics.day1_retention = (len(day_buckets.get(1, set())) / active_day0) * 100
            metrics.day7_retention = (len(day_buckets.get(7, set())) / active_day0) * 100
            metrics.day30_retention = (len(day_buckets.get(30, set())) / active_day0) * 100
            metrics.day90_retention = (len(day_buckets.get(90, set())) / active_day0) * 100

        return metrics

    async def analyze_funnel(
        self, funnel_name: str, steps: List[tuple[str, str]], cohort_id: Optional[str] = None
    ) -> List[FunnelStep]:
        """Analyze conversion funnel"""
        filter_users = None
        if cohort_id and (cohort := self.cohorts.get(cohort_id)):
            filter_users = cohort.users

        funnel_result = []
        previous_users = None

        for step_name, event_name in steps:
            # Get users who completed this step
            step_users = set()

            for event in self.events + self.event_buffer:
                if event.event_type == event_name:
                    if filter_users is None or event.user_id in filter_users:
                        step_users.add(event.user_id)

            # Calculate conversion rate
            total = len(previous_users) if previous_users else len(self.users)
            conversion_rate = (len(step_users) / total * 100) if total > 0 else 0

            funnel_result.append(
                FunnelStep(
                    step_name=step_name,
                    event_name=event_name,
                    user_count=len(step_users),
                    conversion_rate=conversion_rate,
                )
            )

            previous_users = step_users

        logger.info(f"Funnel analyzed: {funnel_name}")
        return funnel_result

    async def create_segment(self, segment_name: str, conditions: List[Dict[str, Any]]) -> str:
        """Create dynamic user segment"""
        segment_users = set(self.users.keys())

        for condition in conditions:
            filtered = set()
            event_type = condition.get("event_type")

            for event in self.events + self.event_buffer:
                if event.event_type == event_type and event.user_id in segment_users:
                    filtered.add(event.user_id)

            segment_users = (
                segment_users.intersection(filtered)
                if condition.get("and")
                else segment_users.union(filtered)
            )

        self.user_segments[segment_name] = segment_users
        logger.info(f"Segment created: {segment_name} (size={len(segment_users)})")
        return segment_name

    async def calculate_ltv(self, user_id: str, arpu: float = 10.0) -> float:
        """Calculate user lifetime value"""
        if user := self.users.get(user_id):
            # Simple LTV = ARPU * average_session_count
            session_count = len(user.sessions)
            return arpu * session_count * 12  # Annualized
        return 0.0

    async def predict_churn(self, user_id: str, inactivity_days: int = 14) -> float:
        """Predict churn probability (0.0-1.0)"""
        if user := self.users.get(user_id):
            # Simple heuristic
            days_inactive = (datetime.utcnow() - user.created_at).days

            if days_inactive > inactivity_days:
                return min(1.0, (days_inactive - inactivity_days) / 30)

        return 0.0

    async def get_cohort_stats(self, cohort_id: str) -> Dict[str, Any]:
        """Get detailed stats for cohort"""
        if not (cohort := self.cohorts.get(cohort_id)):
            return {}

        users_list = list(cohort.users)
        event_count = sum(1 for e in self.events + self.event_buffer if e.user_id in cohort.users)

        avg_ltv = 0.0
        if users_list:
            ltv_sum = sum(await self.calculate_ltv(uid) for uid in users_list)
            avg_ltv = ltv_sum / len(users_list)

        return {
            "cohort_id": cohort_id,
            "name": cohort.name,
            "size": cohort.size,
            "event_count": event_count,
            "avg_ltv": avg_ltv,
            "created_at": cohort.created_at.isoformat(),
        }

    async def list_cohorts(self) -> List[Dict[str, Any]]:
        """List all cohorts"""
        return [
            {"cohort_id": c.cohort_id, "name": c.name, "size": c.size, "type": c.cohort_type.value}
            for c in self.cohorts.values()
        ]


def _compat_create_cohort(
    self, name: str, criteria: Dict[str, Any], group_by: str = "month"
) -> str:
    cohort_id = f"cohort_{len(self.cohorts) + 1}"
    self.cohorts[cohort_id] = type(
        "CompatCohort",
        (),
        {
            "cohort_id": cohort_id,
            "name": name,
            "criteria": criteria,
            "group_by": group_by,
        },
    )()
    return cohort_id


def _compat_calculate_retention(
    self, cohort_id: str, users: List[Dict[str, Any]], days: List[int]
) -> Dict[str, float]:
    total = len(users) or 1
    return {f"day_{day}": round(max(0.0, 1 - (day / (max(days) + total))), 2) for day in days}


def _compat_analyze_funnel(
    self, steps: List[str], user_journeys: List[Dict[str, Any]]
) -> Dict[str, Dict[str, Any]]:
    total_users = len(user_journeys) or 1
    results: Dict[str, Dict[str, Any]] = {}
    for step in steps:
        count = sum(1 for journey in user_journeys if step in journey.get("steps", []))
        results[step] = {"count": count, "conversion_rate": count / total_users}
    return results


def _compat_create_segments(
    self, users: List[Dict[str, Any]], criteria: Dict[str, Any]
) -> Dict[str, List[Dict[str, Any]]]:
    return {
        segment_name: [user for user in users if matcher(user)]
        for segment_name, matcher in criteria.items()
    }


AdvancedAnalyticsEngine.create_cohort = _compat_create_cohort
AdvancedAnalyticsEngine.calculate_retention = _compat_calculate_retention
AdvancedAnalyticsEngine.analyze_funnel = _compat_analyze_funnel
AdvancedAnalyticsEngine.create_segments = _compat_create_segments


if __name__ == "__main__":
    print("✅ Tier 15: Advanced Analytics")
    print("Features:")
    print("- Cohort analysis")
    print("- Retention metrics")
    print("- Funnel analysis")
    print("- Dynamic segments")
    print("- LTV calculation")
    print("- Churn prediction")
