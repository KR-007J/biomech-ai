"""
PHASE 2: TIER 14 - ML MODEL VERSIONING & MANAGEMENT
Model versioning, experiment tracking, model registry
"""

import logging
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class ModelStatus(str, Enum):
    """Model lifecycle status"""

    TRAINING = "training"
    VALIDATING = "validating"
    APPROVED = "approved"
    DEPLOYED = "deployed"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"


class ModelType(str, Enum):
    """Types of models"""

    ENSEMBLE = "ensemble"
    LSTM = "lstm"
    CNN = "cnn"
    TRANSFORMER = "transformer"
    GRADIENT_BOOSTING = "gradient_boosting"


@dataclass
class ModelMetrics:
    """Model performance metrics"""

    accuracy: float = 0.0
    precision: float = 0.0
    recall: float = 0.0
    f1_score: float = 0.0
    auc_roc: float = 0.0
    latency_ms: float = 0.0
    throughput_rps: float = 0.0
    model_size_mb: float = 0.0
    training_time_hours: float = 0.0
    inference_time_ms: float = 0.0


@dataclass
class ModelVersion:
    """Model version metadata"""

    version_id: str = ""
    model_name: str = ""
    version_number: str = ""
    model_type: ModelType = ModelType.ENSEMBLE
    status: ModelStatus = ModelStatus.TRAINING
    created_at: datetime = field(default_factory=datetime.utcnow)
    deployed_at: Optional[datetime] = None
    deprecated_at: Optional[datetime] = None

    # Training info
    training_data_size: int = 0
    training_samples: int = 0
    validation_split: float = 0.2
    test_split: float = 0.1

    # Model details
    framework: str = ""  # tensorflow, pytorch, sklearn
    model_hash: str = ""  # SHA256 of model file
    model_size_mb: float = 0.0
    parameters: Dict[str, Any] = field(default_factory=dict)
    hyperparameters: Dict[str, Any] = field(default_factory=dict)

    # Performance metrics
    metrics: ModelMetrics = field(default_factory=ModelMetrics)

    # Lineage
    parent_version: Optional[str] = None
    training_branch: str = ""
    git_commit: str = ""

    # Deployment
    deployment_environment: str = ""  # staging, production
    traffic_percentage: float = 100.0
    canary_metrics: Dict[str, float] = field(default_factory=dict)

    # Comparison with previous
    performance_delta: Dict[str, float] = field(default_factory=dict)
    inference_time_delta_pct: float = 0.0


@dataclass
class ExperimentRun:
    """ML experiment tracking"""

    run_id: str = ""
    experiment_name: str = ""
    model_type: ModelType = ModelType.ENSEMBLE
    status: str = "in_progress"
    start_time: datetime = field(default_factory=datetime.utcnow)
    end_time: Optional[datetime] = None
    duration_seconds: float = 0.0

    # Configuration
    config: Dict[str, Any] = field(default_factory=dict)

    # Metrics during training
    metrics_history: Dict[str, List[float]] = field(default_factory=dict)
    best_metrics: ModelMetrics = field(default_factory=ModelMetrics)

    # Artifacts
    artifacts: Dict[str, str] = field(default_factory=dict)  # name -> path

    # Notes
    notes: str = ""
    tags: List[str] = field(default_factory=list)


class ModelRegistry:
    """
    ML Model registry and version management

    Features:
    - Model versioning and history
    - Experiment tracking
    - Model comparison
    - Canary deployments
    - A/B testing integration
    - Model promotion workflow
    - Performance monitoring
    """

    def __init__(self):
        self.models: Dict[str, List[ModelVersion]] = {}  # model_name -> versions
        self.current_deployed: Dict[str, ModelVersion] = {}  # env -> current model
        self.experiments: Dict[str, ExperimentRun] = {}
        self.model_lineage: Dict[str, List[str]] = {}  # model_name -> version_ids
        self.performance_history: Dict[str, List[Dict]] = {}

    async def register_model(
        self,
        model_name: str,
        model_type: ModelType,
        framework: str,
        metrics: ModelMetrics,
        hyperparameters: Dict[str, Any],
        training_data_size: int,
    ) -> ModelVersion:
        """Register new model version"""
        if model_name not in self.models:
            self.models[model_name] = []
            self.model_lineage[model_name] = []

        versions = self.models[model_name]
        version_number = f"v{len(versions) + 1}.0.0"

        model_version = ModelVersion(
            version_id=f"{model_name}_{version_number}",
            model_name=model_name,
            version_number=version_number,
            model_type=model_type,
            status=ModelStatus.VALIDATING,
            framework=framework,
            metrics=metrics,
            hyperparameters=hyperparameters,
            training_data_size=training_data_size,
        )

        versions.append(model_version)
        self.model_lineage[model_name].append(model_version.version_id)

        logger.info(f"Model registered: {model_version.version_id}")
        return model_version

    async def approve_model(self, version_id: str) -> bool:
        """Approve model for deployment"""
        for versions in self.models.values():
            for model in versions:
                if model.version_id == version_id:
                    model.status = ModelStatus.APPROVED
                    logger.info(f"Model approved: {version_id}")
                    return True
        return False

    async def deploy_model(self, version_id: str, environment: str, traffic_percentage: float = 100.0) -> bool:
        """Deploy model version"""
        for versions in self.models.values():
            for model in versions:
                if model.version_id == version_id:
                    if model.status != ModelStatus.APPROVED:
                        logger.error(f"Cannot deploy non-approved model: {version_id}")
                        return False

                    # Canary deployment
                    if traffic_percentage < 100.0:
                        model.status = ModelStatus.DEPLOYED
                        model.traffic_percentage = traffic_percentage
                        logger.info(f"Canary deployment: {version_id} ({traffic_percentage}%)")
                    else:
                        model.status = ModelStatus.DEPLOYED
                        model.deployed_at = datetime.utcnow()
                        self.current_deployed[environment] = model
                        logger.info(f"Model deployed to {environment}: {version_id}")

                    return True
        return False

    async def compare_models(self, version_id1: str, version_id2: str) -> Dict[str, Any]:
        """Compare two model versions"""
        model1 = self._get_model_by_id(version_id1)
        model2 = self._get_model_by_id(version_id2)

        if not model1 or not model2:
            return {}

        return {
            "model1": {
                "version_id": model1.version_id,
                "metrics": asdict(model1.metrics),
            },
            "model2": {
                "version_id": model2.version_id,
                "metrics": asdict(model2.metrics),
            },
            "deltas": {
                "accuracy_delta": model2.metrics.accuracy - model1.metrics.accuracy,
                "latency_delta_ms": model2.metrics.latency_ms - model1.metrics.latency_ms,
                "f1_delta": model2.metrics.f1_score - model1.metrics.f1_score,
            },
        }

    async def track_experiment(self, experiment_name: str, model_type: ModelType, config: Dict[str, Any]) -> str:
        """Start experiment run"""
        run = ExperimentRun(
            run_id=f"{experiment_name}_{int(datetime.utcnow().timestamp())}",
            experiment_name=experiment_name,
            model_type=model_type,
            config=config,
        )

        self.experiments[run.run_id] = run
        logger.info(f"Experiment started: {run.run_id}")
        return run.run_id

    async def log_experiment_metric(self, run_id: str, metric_name: str, value: float, step: int = 0) -> bool:
        """Log metric during experiment"""
        if run := self.experiments.get(run_id):
            if metric_name not in run.metrics_history:
                run.metrics_history[metric_name] = []
            run.metrics_history[metric_name].append(value)
            return True
        return False

    async def complete_experiment(self, run_id: str, metrics: ModelMetrics) -> bool:
        """Complete experiment run"""
        if run := self.experiments.get(run_id):
            run.end_time = datetime.utcnow()
            run.duration_seconds = (run.end_time - run.start_time).total_seconds()
            run.best_metrics = metrics
            run.status = "completed"
            logger.info(f"Experiment completed: {run_id}")
            return True
        return False

    async def rollback_model(self, environment: str) -> bool:
        """Rollback to previous model version"""
        if environment not in self.current_deployed:
            return False

        current = self.current_deployed[environment]

        # Find previous version
        for versions in self.models.values():
            idx = versions.index(current)
            if idx > 0:
                previous = versions[idx - 1]
                self.current_deployed[environment] = previous
                logger.info(f"Rolled back to: {previous.version_id}")
                return True

        return False

    async def get_model_history(self, model_name: str) -> List[ModelVersion]:
        """Get version history for a model"""
        return self.models.get(model_name, [])

    async def get_current_model(self, environment: str) -> Optional[ModelVersion]:
        """Get currently deployed model"""
        return self.current_deployed.get(environment)

    async def deprecate_model(self, version_id: str) -> bool:
        """Mark model as deprecated"""
        if model := self._get_model_by_id(version_id):
            model.status = ModelStatus.DEPRECATED
            model.deprecated_at = datetime.utcnow()
            logger.info(f"Model deprecated: {version_id}")
            return True
        return False

    def _get_model_by_id(self, version_id: str) -> Optional[ModelVersion]:
        """Get model by version ID"""
        for versions in self.models.values():
            for model in versions:
                if model.version_id == version_id:
                    return model
        return None

    async def get_model_performance_trend(self, model_name: str) -> List[Dict]:
        """Get performance trend for model"""
        versions = self.models.get(model_name, [])
        trend = []

        for version in versions:
            trend.append(
                {
                    "version": version.version_number,
                    "accuracy": version.metrics.accuracy,
                    "latency_ms": version.metrics.latency_ms,
                    "status": version.status.value,
                    "deployed_at": (version.deployed_at.isoformat() if version.deployed_at else None),
                }
            )

        return trend


@dataclass
class CompatibilityModel:
    model_id: str
    name: str
    version: str
    model_type: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    status: str = "VALIDATING"
    metrics: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CompatibilityExperiment:
    experiment_id: str
    name: str
    model_type: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    status: str = "RUNNING"
    metrics: Dict[str, Any] = field(default_factory=dict)


def _compat_register_model(
    self,
    name: str,
    version: str,
    model_type: str,
    metadata: Optional[Dict[str, Any]] = None,
) -> str:
    model_id = f"{name}_{version}"
    self.models[model_id] = CompatibilityModel(
        model_id=model_id,
        name=name,
        version=version,
        model_type=model_type,
        metadata=metadata or {},
        metrics=dict(metadata or {}),
    )
    return model_id


def _compat_approve_model(self, model_id: str, approved_by: Optional[str] = None) -> bool:
    if model_id not in self.models:
        return False
    self.models[model_id].status = "APPROVED"
    return True


def _compat_update_metrics(self, model_id: str, metrics: Dict[str, Any]) -> bool:
    if model_id not in self.models:
        return False
    self.models[model_id].metrics.update(metrics)
    return True


def _compat_compare_models(self, model_id1: str, model_id2: str) -> Dict[str, Dict[str, Any]]:
    model1 = self.models[model_id1]
    model2 = self.models[model_id2]
    return {model1.name: model1.metrics, model2.name: model2.metrics}


def _compat_start_experiment(self, name: str, model_type: str, parameters: Dict[str, Any]) -> str:
    experiment_id = f"{name}_{len(self.experiments) + 1}"
    self.experiments[experiment_id] = CompatibilityExperiment(
        experiment_id=experiment_id,
        name=name,
        model_type=model_type,
        parameters=parameters,
    )
    return experiment_id


def _compat_end_experiment(self, experiment_id: str, metrics: Dict[str, Any]) -> bool:
    if experiment_id not in self.experiments:
        return False
    experiment = self.experiments[experiment_id]
    experiment.status = "COMPLETED"
    experiment.metrics.update(metrics)
    return True


ModelRegistry.register_model = _compat_register_model
ModelRegistry.approve_model = _compat_approve_model
ModelRegistry.update_metrics = _compat_update_metrics
ModelRegistry.compare_models = _compat_compare_models
ModelRegistry.start_experiment = _compat_start_experiment
ModelRegistry.end_experiment = _compat_end_experiment


if __name__ == "__main__":
    print("✅ Tier 14: ML Model Versioning")
    print("Features:")
    print("- Model versioning and history")
    print("- Experiment tracking")
    print("- Model comparison")
    print("- Canary deployments")
    print("- Performance monitoring")
    print("- Rollback capability")
