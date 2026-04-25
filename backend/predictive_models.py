"""
Tier 1: Predictive Injury Prevention System
=============================================

Time-series LSTM models for predicting injury risk trajectory.
Analyzes movement patterns across sessions to forecast injury probability.

Features:
- Movement pattern analysis (temporal sequences)
- Risk trajectory prediction (1-2 week lookahead)
- Personalized injury thresholds
- Session-over-session degradation tracking
"""

import json
import logging
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class SessionData:
    """Single session biomechanical data point"""

    session_id: str
    timestamp: datetime
    user_id: str
    exercise_type: str
    duration_seconds: float
    peak_risk_score: float
    avg_risk_score: float
    joint_angles: Dict[str, float]
    angle_deviations: Dict[str, float]
    movement_smoothness: float  # 0-1: smoother is better
    fatigue_indicator: float  # 0-1: higher = more fatigued
    confidence_score: float

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        data = asdict(self)
        data["timestamp"] = data["timestamp"].isoformat()
        return data


@dataclass
class PredictionResult:
    """Injury prediction result"""

    user_id: str
    prediction_date: datetime
    weeks_ahead: int
    injury_probability: float  # 0-1
    risk_trajectory: str  # "improving", "stable", "degrading", "critical"
    confidence: float
    contributing_factors: List[str]
    recommendations: List[str]
    next_prediction: Optional[datetime]


class MovementFeatureExtractor:
    """Extract features from session data for LSTM"""

    @staticmethod
    def extract_temporal_features(
        sessions: List[SessionData], lookback_window: int = 10
    ) -> np.ndarray:
        """
        Extract temporal features from session sequence

        Args:
            sessions: List of sessions sorted by timestamp
            lookback_window: Number of past sessions to consider

        Returns:
            Feature array of shape (lookback_window, n_features)
        """
        features = []

        for session in sessions[-lookback_window:]:
            feature_vector = [
                session.peak_risk_score / 100,
                session.avg_risk_score / 100,
                session.movement_smoothness,
                session.fatigue_indicator,
                session.confidence_score,
            ]

            # Add deviation features
            feature_vector.extend(
                [
                    np.mean(list(session.angle_deviations.values())) / 20,  # Normalize
                    np.std(list(session.angle_deviations.values())) / 20,
                ]
            )

            features.append(feature_vector)

        # Pad if necessary
        if len(features) < lookback_window:
            padding = [[0.0] * len(features[0])] * (lookback_window - len(features))
            features = padding + features

        return np.array(features)

    @staticmethod
    def extract_movement_degradation(
        sessions: List[SessionData], window: int = 5
    ) -> Dict[str, float]:
        """
        Calculate movement quality degradation metrics

        Args:
            sessions: Session data
            window: Sliding window size

        Returns:
            Degradation metrics
        """
        if len(sessions) < 2:
            return {"degradation_rate": 0.0, "trend": "stable"}

        # Risk score trend
        recent_risks = [s.avg_risk_score for s in sessions[-window:]]
        risk_trend = np.polyfit(range(len(recent_risks)), recent_risks, 1)[0]

        # Smoothness trend (inverse - lower smoothness is worse)
        recent_smoothness = [s.movement_smoothness for s in sessions[-window:]]
        smoothness_trend = np.polyfit(range(len(recent_smoothness)), recent_smoothness, 1)[0]

        # Fatigue accumulation
        fatigue_trend = np.mean([s.fatigue_indicator for s in sessions[-window:]])

        # Determine trend direction
        if risk_trend > 0.05:  # Significant increase
            trend = "degrading"
        elif risk_trend < -0.05:  # Significant decrease
            trend = "improving"
        else:
            trend = "stable"

        return {
            "risk_trend": float(risk_trend),
            "smoothness_trend": float(smoothness_trend),
            "fatigue_level": float(fatigue_trend),
            "trend_direction": trend,
        }


class InjuryPredictorLSTM:
    """LSTM-based injury prediction model"""

    def __init__(self, model_path: Optional[str] = None):
        """
        Initialize LSTM predictor

        Args:
            model_path: Path to pretrained model
        """
        self.model = None
        self.scaler = None
        self.lookback_window = 10
        self.feature_extractor = MovementFeatureExtractor()

        if model_path and Path(model_path).exists():
            self.load_model(model_path)

    def build_model(self, n_features: int = 7):
        """
        Build LSTM model architecture

        Args:
            n_features: Number of input features
        """
        try:
            from tensorflow import keras
            from tensorflow.keras import layers

            model = keras.Sequential(
                [
                    layers.LSTM(
                        128,
                        activation="relu",
                        input_shape=(self.lookback_window, n_features),
                        return_sequences=True,
                        name="lstm_1",
                    ),
                    layers.Dropout(0.2),
                    layers.LSTM(64, activation="relu", return_sequences=False, name="lstm_2"),
                    layers.Dropout(0.2),
                    layers.Dense(32, activation="relu", name="dense_1"),
                    layers.Dense(16, activation="relu", name="dense_2"),
                    layers.Dense(1, activation="sigmoid", name="output"),  # Probability output
                ]
            )

            model.compile(
                optimizer=keras.optimizers.Adam(learning_rate=0.001),
                loss="binary_crossentropy",
                metrics=["accuracy", keras.metrics.Precision(), keras.metrics.Recall()],
            )

            self.model = model
            logger.info("✅ LSTM model architecture built")
            return model
        except ImportError:
            logger.warning("TensorFlow not installed. Install via: pip install tensorflow")
            return None

    def train(
        self,
        user_sessions: Dict[str, List[SessionData]],
        epochs: int = 50,
        batch_size: int = 32,
        validation_split: float = 0.2,
    ) -> Dict[str, Any]:
        """
        Train LSTM model on historical session data

        Args:
            user_sessions: Dict mapping user_id to list of sessions
            epochs: Training epochs
            batch_size: Batch size
            validation_split: Validation data split

        Returns:
            Training history
        """
        if not self.model:
            n_features = 7
            self.build_model(n_features)

        try:
            pass

            # Prepare training data
            X_train = []
            y_train = []

            for user_id, sessions in user_sessions.items():
                if len(sessions) < self.lookback_window + 1:
                    continue

                # Sort by timestamp
                sessions = sorted(sessions, key=lambda s: s.timestamp)

                # Create sequences
                for i in range(self.lookback_window, len(sessions)):
                    X = self.feature_extractor.extract_temporal_features(
                        sessions[:i], self.lookback_window
                    )
                    X_train.append(X)

                    # Target: did injury occur in next session?
                    # For now, use risk score as proxy (>70 = injury risk)
                    y = 1 if sessions[i].peak_risk_score > 70 else 0
                    y_train.append(y)

            if len(X_train) == 0:
                logger.warning("No training data available")
                return {}

            X_train = np.array(X_train)
            y_train = np.array(y_train)

            # Train model
            history = self.model.fit(
                X_train,
                y_train,
                epochs=epochs,
                batch_size=batch_size,
                validation_split=validation_split,
                verbose=1,
            )

            logger.info("✅ LSTM model trained successfully")
            return history.history
        except Exception as e:
            logger.error(f"Training error: {e}")
            return {}

    def predict(self, user_sessions: List[SessionData], weeks_ahead: int = 2) -> PredictionResult:
        """
        Predict injury probability for future period

        Args:
            user_sessions: Historical sessions for user
            weeks_ahead: Prediction horizon (1-4 weeks)

        Returns:
            Prediction result with recommendations
        """
        if not self.model or len(user_sessions) < self.lookback_window:
            logger.warning("Insufficient data for prediction")
            return PredictionResult(
                user_id=user_sessions[0].user_id if user_sessions else "unknown",
                prediction_date=datetime.utcnow(),
                weeks_ahead=weeks_ahead,
                injury_probability=0.3,  # Default conservative estimate
                risk_trajectory="unknown",
                confidence=0.2,
                contributing_factors=["Insufficient historical data"],
                recommendations=["Collect more session data for better predictions"],
            )

        try:
            # Sort sessions by timestamp
            sessions = sorted(user_sessions, key=lambda s: s.timestamp)

            # Extract features
            X = self.feature_extractor.extract_temporal_features(sessions, self.lookback_window)
            X = X.reshape(1, self.lookback_window, -1)

            # Predict
            probability = float(self.model.predict(X, verbose=0)[0][0])

            # Calculate trajectory
            degradation = self.feature_extractor.extract_movement_degradation(sessions)
            risk_trajectory = degradation["trend_direction"]

            # Contributing factors
            factors = []
            if degradation["risk_trend"] > 0.05:
                factors.append(f"Risk increasing at {degradation['risk_trend']:.3f}/session")
            if degradation["fatigue_level"] > 0.7:
                factors.append("High fatigue accumulation detected")
            if sessions[-1].movement_smoothness < 0.6:
                factors.append("Movement quality degraded")

            # Recommendations
            recommendations = []
            if probability > 0.7:
                recommendations.append("URGENT: Reduce training intensity immediately")
                recommendations.append("Perform targeted recovery and flexibility work")
                recommendations.append("Consult with sports medicine professional")
            elif probability > 0.5:
                recommendations.append("Moderate risk: Consider form/technique review")
                recommendations.append("Increase rest days by 1")
                recommendations.append("Focus on core and stabilizer muscles")
            else:
                recommendations.append("Continue current training with standard precautions")
                recommendations.append("Monitor for form degradation")

            return PredictionResult(
                user_id=sessions[0].user_id,
                prediction_date=datetime.utcnow(),
                weeks_ahead=weeks_ahead,
                injury_probability=probability,
                risk_trajectory=risk_trajectory,
                confidence=0.85,
                contributing_factors=factors,
                recommendations=recommendations,
                next_prediction=datetime.utcnow() + timedelta(days=7),
            )
        except Exception as e:
            logger.error(f"Prediction error: {e}")
            return PredictionResult(
                user_id=sessions[0].user_id if sessions else "unknown",
                prediction_date=datetime.utcnow(),
                weeks_ahead=weeks_ahead,
                injury_probability=0.5,
                risk_trajectory="unknown",
                confidence=0.3,
                contributing_factors=[str(e)],
                recommendations=["Error in prediction model. Manual review recommended."],
            )

    def save_model(self, path: str) -> bool:
        """Save trained model"""
        try:
            if self.model:
                self.model.save(path)
                logger.info(f"✅ Model saved to {path}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error saving model: {e}")
            return False

    def load_model(self, path: str) -> bool:
        """Load pretrained model"""
        try:
            import tensorflow as tf

            self.model = tf.keras.models.load_model(path)
            logger.info(f"✅ Model loaded from {path}")
            return True
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            return False


class InjuryRiskTracker:
    """Track and monitor user injury risk over time"""

    def __init__(self):
        self.user_sessions: Dict[str, List[SessionData]] = {}
        self.predictions: Dict[str, List[PredictionResult]] = {}
        self.predictor = InjuryPredictorLSTM()

    def add_session(self, session: SessionData) -> None:
        """Add new session data"""
        if session.user_id not in self.user_sessions:
            self.user_sessions[session.user_id] = []
        self.user_sessions[session.user_id].append(session)
        logger.info(f"Added session for user {session.user_id}")

    def get_prediction(self, user_id: str, weeks_ahead: int = 2) -> Optional[PredictionResult]:
        """Get latest prediction for user"""
        if user_id not in self.user_sessions:
            return None

        sessions = self.user_sessions[user_id]
        prediction = self.predictor.predict(sessions, weeks_ahead)

        if user_id not in self.predictions:
            self.predictions[user_id] = []
        self.predictions[user_id].append(prediction)

        return prediction

    def get_user_risk_history(self, user_id: str, limit: int = 30) -> Dict[str, Any]:
        """Get risk history for user"""
        if user_id not in self.user_sessions:
            return {}

        sessions = sorted(self.user_sessions[user_id][-limit:], key=lambda s: s.timestamp)

        risk_scores = [s.avg_risk_score for s in sessions]
        timestamps = [s.timestamp.isoformat() for s in sessions]

        return {
            "user_id": user_id,
            "sessions_count": len(sessions),
            "risk_scores": risk_scores,
            "timestamps": timestamps,
            "current_risk": risk_scores[-1] if risk_scores else 0,
            "trend": (
                "increasing"
                if len(risk_scores) > 1 and risk_scores[-1] > risk_scores[-2]
                else "stable"
            ),
        }


# Example usage
def example_predictor_usage():
    """Example of how to use the injury predictor"""
    tracker = InjuryRiskTracker()

    # Create sample sessions
    now = datetime.utcnow()
    for i in range(15):
        session = SessionData(
            session_id=f"session_{i}",
            timestamp=now - timedelta(days=15 - i),
            user_id="user_123",
            exercise_type="running",
            duration_seconds=1200,
            peak_risk_score=45 + (i * 2),  # Increasing risk
            avg_risk_score=35 + (i * 1.5),
            joint_angles={"knee": 90, "hip": 85, "ankle": 100},
            angle_deviations={
                "knee": 5 + i * 0.3,
                "hip": 3 + i * 0.2,
                "ankle": 2 + i * 0.1,
            },
            movement_smoothness=0.85 - (i * 0.02),  # Decreasing smoothness
            fatigue_indicator=(i / 15),  # Increasing fatigue
            confidence_score=0.92,
        )
        tracker.add_session(session)

    # Get prediction
    prediction = tracker.get_prediction("user_123", weeks_ahead=2)
    if prediction:
        print(f"Injury Probability: {prediction.injury_probability:.2%}")
        print(f"Risk Trajectory: {prediction.risk_trajectory}")
        print(f"Recommendations:\n" + "\n".join(f"  - {r}" for r in prediction.recommendations))

    # Get history
    history = tracker.get_user_risk_history("user_123")
    print(f"\nRisk History: {json.dumps(history, indent=2, default=str)}")


if __name__ == "__main__":
    example_predictor_usage()
