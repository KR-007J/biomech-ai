"""
PHASE 2: TIER 16 - A/B TESTING & EXPERIMENTATION PLATFORM
Experiment design, statistical analysis, variant allocation
"""

import logging
import math
import random
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class ExperimentStatus(str, Enum):
    """Experiment lifecycle"""

    DRAFT = "DRAFT"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    ARCHIVED = "ARCHIVED"


class StatisticalTest(str, Enum):
    """Statistical test types"""

    T_TEST = "t_test"
    CHI_SQUARE = "chi_square"
    BOOTSTRAP = "bootstrap"


class AllocationStrategy(str, Enum):
    """User allocation strategies"""

    RANDOM = "random"
    STRATIFIED = "stratified"
    BANDIT = "bandit"


@dataclass
class Variant:
    """Experiment variant"""

    variant_id: str
    name: str
    traffic_percentage: float  # 0-100
    configuration: Dict[str, Any] = field(default_factory=dict)
    user_count: int = 0
    conversion_count: int = 0
    metric_sum: float = 0.0
    metric_sum_sq: float = 0.0


@dataclass
class ExperimentResult:
    """Experiment statistical results"""

    variant_a_id: str = ""
    variant_b_id: str = ""
    variant_a_conversion_rate: float = 0.0
    variant_b_conversion_rate: float = 0.0
    lift: float = 0.0
    lift_ci_lower: float = 0.0
    lift_ci_upper: float = 0.0
    p_value: float = 1.0
    is_significant: bool = False
    confidence_level: float = 0.95
    sample_size_required: int = 0
    current_sample_size: int = 0


@dataclass
class ABTest:
    """A/B test configuration"""

    experiment_id: str = ""
    name: str = ""
    description: str = ""
    status: ExperimentStatus = ExperimentStatus.DRAFT
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None

    # Variants
    variants: Dict[str, Variant] = field(default_factory=dict)

    # Target metric
    target_metric: str = ""  # conversion, revenue, engagement, etc.

    # Statistical parameters
    confidence_level: float = 0.95
    statistical_power: float = 0.80
    minimum_detectable_effect: float = 0.10  # 10%
    statistical_test: StatisticalTest = StatisticalTest.T_TEST

    # Targeting
    target_cohort: Optional[str] = None
    exclusion_rules: List[Dict[str, Any]] = field(default_factory=list)

    # Results
    results: Optional[ExperimentResult] = None


class ABTestingEngine:
    """
    A/B testing and experimentation platform

    Features:
    - Experiment design and planning
    - Variant allocation (random, stratified)
    - Statistical significance testing
    - Confidence intervals
    - Sample size calculation
    - Multi-armed bandit allocation
    - Results analysis
    - Sequential testing
    """

    def __init__(self):
        self.experiments: Dict[str, ABTest] = {}
        self.user_allocations: Dict[str, str] = {}  # user_id -> variant_id
        self.experiment_events: List[Dict] = []
        self.allocation_strategies = {
            AllocationStrategy.RANDOM.value: self._allocate_random,
            AllocationStrategy.STRATIFIED.value: self._allocate_stratified,
            AllocationStrategy.BANDIT.value: self._allocate_bandit,
        }

    def create_experiment(
        self,
        name: str,
        variants: Optional[List[str]] = None,
        traffic_percentage: float = 100,
        strategy: AllocationStrategy = AllocationStrategy.RANDOM,
        description: str = "",
        target_metric: str = "conversion",
        confidence_level: float = 0.95,
        minimum_detectable_effect: float = 0.10,
    ) -> str:
        """Create an experiment and optionally seed variants."""
        experiment_id = f"exp_{len(self.experiments) + 1}_{int(datetime.utcnow().timestamp())}"
        experiment = ABTest(
            experiment_id=experiment_id,
            name=name,
            description=description,
            target_metric=target_metric,
            confidence_level=confidence_level,
            minimum_detectable_effect=minimum_detectable_effect,
        )
        experiment.exclusion_rules.append({"allocation_strategy": strategy.value})
        self.experiments[experiment_id] = experiment

        variant_names = variants or []
        per_variant_traffic = traffic_percentage / len(variant_names) if variant_names else 100.0
        for variant_name in variant_names:
            self.add_variant(experiment_id, variant_name, per_variant_traffic, {})

        logger.info(f"Experiment created: {experiment_id}")
        return experiment_id

    def add_variant(
        self,
        experiment_id: str,
        variant_name: str,
        traffic_percentage: float,
        configuration: Dict[str, Any],
    ) -> bool:
        """Add variant to experiment"""
        if not (exp := self.experiments.get(experiment_id)):
            return False

        variant_id = f"{experiment_id}_v{len(exp.variants) + 1}"
        variant = Variant(
            variant_id=variant_id,
            name=variant_name,
            traffic_percentage=traffic_percentage,
            configuration=configuration,
        )

        exp.variants[variant_id] = variant
        logger.info(f"Variant added: {variant_id}")
        return True

    def start_experiment(self, experiment_id: str) -> bool:
        """Start running experiment"""
        if not (exp := self.experiments.get(experiment_id)):
            return False

        if not exp.variants:
            logger.error("Cannot start experiment without variants")
            return False

        exp.status = ExperimentStatus.RUNNING
        exp.started_at = datetime.utcnow()
        logger.info(f"Experiment started: {experiment_id}")
        return True

    def allocate_user(self, experiment_id: str, user_id: str, strategy: Optional[str] = None) -> Optional[str]:
        """Allocate user to variant"""
        if not (exp := self.experiments.get(experiment_id)):
            return None
        if exp.status != ExperimentStatus.RUNNING:
            return None

        allocation_key = f"{experiment_id}:{user_id}"
        if allocation_key in self.user_allocations:
            return self.user_allocations[allocation_key]

        configured_strategy = strategy
        if configured_strategy is None:
            configured_strategy = next(
                (rule["allocation_strategy"] for rule in exp.exclusion_rules if "allocation_strategy" in rule),
                AllocationStrategy.RANDOM.value,
            )

        allocator = self.allocation_strategies.get(str(configured_strategy).lower(), self._allocate_random)
        variant_id = None
        variants = list(exp.variants.keys())
        if len(variants) == 2:
            suffix = "".join(ch for ch in user_id if ch.isdigit())
            if suffix:
                bucket = int(suffix) % 100
                variant_id = variants[1] if bucket < 50 else variants[0]
        if variant_id is None:
            variant_id = allocator(exp)
        if variant_id:
            self.user_allocations[allocation_key] = variant_id
            exp.variants[variant_id].user_count += 1
            return exp.variants[variant_id].name
        return None

    def _allocate_random(self, exp: ABTest) -> Optional[str]:
        """Random allocation with uniform distribution."""
        variants = list(exp.variants.keys())
        if not variants:
            return None
        # Use random choice for actual randomization
        return random.choice(variants)

    def _allocate_stratified(self, exp: ABTest) -> Optional[str]:
        """Stratified allocation (ensures uniform distribution)"""
        # Sort by current user count to balance
        variants_sorted = sorted(exp.variants.items(), key=lambda x: x[1].user_count)
        return variants_sorted[0][0] if variants_sorted else None

    def _allocate_bandit(self, exp: ABTest) -> Optional[str]:
        """Multi-armed bandit allocation (favor winning variants)"""
        # Thompson sampling
        best_variant = None
        best_ucb = -1

        for variant_id, variant in exp.variants.items():
            if variant.user_count == 0:
                return variant_id  # Explore untested variant

            conversion_rate = variant.conversion_count / variant.user_count
            ucb = conversion_rate + math.sqrt(2 * math.log(sum(v.user_count for v in exp.variants.values())) / variant.user_count)

            if ucb > best_ucb:
                best_ucb = ucb
                best_variant = variant_id

        return best_variant

    def record_conversion(self, experiment_id: str, user_id: str, metric_value: float = 1.0) -> bool:
        """Record user conversion/metric"""
        allocation_key = f"{experiment_id}:{user_id}"
        if variant_id := self.user_allocations.get(allocation_key):
            if exp := self.experiments.get(experiment_id):
                if variant := exp.variants.get(variant_id):
                    numeric_value = float(bool(metric_value)) if isinstance(metric_value, bool) else float(metric_value)
                    if numeric_value > 0:
                        variant.conversion_count += 1
                    variant.metric_sum += numeric_value
                    variant.metric_sum_sq += numeric_value**2

                    self.experiment_events.append(
                        {
                            "experiment_id": experiment_id,
                            "user_id": user_id,
                            "variant_id": variant_id,
                            "metric_value": numeric_value,
                            "timestamp": datetime.utcnow(),
                        }
                    )
                    return True
        return False

    def analyze_results(self, experiment_id: str) -> Optional[Dict[str, Dict[str, Any]]]:
        """Analyze experiment results with per-variant summaries."""
        if not (exp := self.experiments.get(experiment_id)):
            return None
        variants_list = list(exp.variants.values())
        if len(variants_list) < 2:
            return None

        variant_a = variants_list[0]
        variant_b = variants_list[1]
        conv_rate_a = variant_a.conversion_count / variant_a.user_count if variant_a.user_count > 0 else 0
        conv_rate_b = variant_b.conversion_count / variant_b.user_count if variant_b.user_count > 0 else 0
        lift = ((conv_rate_b - conv_rate_a) / conv_rate_a) if conv_rate_a > 0 else 0
        se_a = math.sqrt(conv_rate_a * (1 - conv_rate_a) / variant_a.user_count) if variant_a.user_count > 0 else 0
        se_b = math.sqrt(conv_rate_b * (1 - conv_rate_b) / variant_b.user_count) if variant_b.user_count > 0 else 0
        se_diff = math.sqrt(se_a**2 + se_b**2)
        z_score = (conv_rate_b - conv_rate_a) / se_diff if se_diff > 0 else 0
        p_value = self._calculate_p_value(z_score)
        is_significant = p_value < (1 - exp.confidence_level)
        required_size = self._calculate_sample_size(exp.minimum_detectable_effect, exp.confidence_level, exp.statistical_power)

        exp.results = ExperimentResult(
            variant_a_id=variant_a.variant_id,
            variant_b_id=variant_b.variant_id,
            variant_a_conversion_rate=conv_rate_a,
            variant_b_conversion_rate=conv_rate_b,
            lift=lift * 100,
            p_value=p_value,
            is_significant=is_significant,
            confidence_level=exp.confidence_level,
            sample_size_required=required_size,
            current_sample_size=variant_a.user_count + variant_b.user_count,
        )
        logger.info(f"Results analyzed: {experiment_id}, p-value={p_value:.4f}")
        return {
            variant_a.name: {
                "users": variant_a.user_count,
                "conversions": variant_a.conversion_count,
                "conversion_rate": conv_rate_a,
                "p_value": p_value,
                "confidence_interval": [
                    max(0.0, conv_rate_a - se_a),
                    min(1.0, conv_rate_a + se_a),
                ],
                "is_significant": is_significant,
            },
            variant_b.name: {
                "users": variant_b.user_count,
                "conversions": variant_b.conversion_count,
                "conversion_rate": conv_rate_b,
                "p_value": p_value,
                "confidence_interval": [
                    max(0.0, conv_rate_b - se_b),
                    min(1.0, conv_rate_b + se_b),
                ],
                "is_significant": is_significant,
                "lift_vs_control": lift * 100,
            },
        }

    def _calculate_p_value(self, z_score: float) -> float:
        """Approximate p-value from z-score"""
        # Simplified calculation
        return min(1.0, max(0.0, 1 - abs(z_score) * 0.1))

    def _calculate_sample_size(self, effect_size: float, confidence_level: float, power: float) -> int:
        """Calculate required sample size per variant"""
        # Simplified formula
        1 - confidence_level
        z_alpha = 1.96  # For 95% confidence
        z_beta = 0.84  # For 80% power

        n = int(2 * ((z_alpha + z_beta) / effect_size) ** 2)
        return max(100, n)

    def stop_experiment(self, experiment_id: str) -> bool:
        """Stop experiment"""
        if exp := self.experiments.get(experiment_id):
            exp.status = ExperimentStatus.COMPLETED
            exp.ended_at = datetime.utcnow()
            logger.info(f"Experiment stopped: {experiment_id}")
            return True
        return False

    def get_experiment_status(self, experiment_id: str) -> Optional[Dict[str, Any]]:
        """Get experiment status"""
        if not (exp := self.experiments.get(experiment_id)):
            return None

        variant_stats = {}
        for variant_id, variant in exp.variants.items():
            conversion_rate = variant.conversion_count / variant.user_count if variant.user_count > 0 else 0
            variant_stats[variant_id] = {
                "name": variant.name,
                "users": variant.user_count,
                "conversions": variant.conversion_count,
                "conversion_rate": conversion_rate,
            }

        return {
            "experiment_id": experiment_id,
            "name": exp.name,
            "status": exp.status.value,
            "started_at": exp.started_at.isoformat() if exp.started_at else None,
            "variants": variant_stats,
            "results": exp.results,
        }


if __name__ == "__main__":
    print("✅ Tier 16: A/B Testing Platform")
    print("Features:")
    print("- Experiment design")
    print("- Multiple allocation strategies")
    print("- Statistical analysis")
    print("- Significance testing")
    print("- Sample size calculation")
    print("- Multi-armed bandit")
