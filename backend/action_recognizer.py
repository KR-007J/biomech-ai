"""
Tier 3: Action Recognition System
==================================

Automatically detect and classify exercises/movements:
- Exercise classification (squat, bench press, running, etc.)
- Form verification
- Transition detection
- Sport-specific move recognition
- Real-time action labeling
"""

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)


class ExerciseType(Enum):
    """Common exercise types"""

    SQUAT = "squat"
    DEADLIFT = "deadlift"
    BENCH_PRESS = "bench_press"
    PULL_UP = "pull_up"
    PUSH_UP = "push_up"
    RUNNING = "running"
    WALKING = "walking"
    STANDING = "standing"
    JUMPING = "jumping"
    LUNGE = "lunge"
    SHOULDER_PRESS = "shoulder_press"
    UNKNOWN = "unknown"


class MovementPhase(Enum):
    """Movement phases"""

    PREPARATION = "preparation"
    CONCENTRIC = "concentric"  # Muscle shortens
    ISOMETRIC = "isometric"  # Static
    ECCENTRIC = "eccentric"  # Muscle lengthens
    RETURN = "return"
    REST = "rest"


@dataclass
class DetectedAction:
    """Detected action/exercise"""

    action_type: ExerciseType
    confidence: float  # 0-1
    phase: MovementPhase
    start_frame: int
    end_frame: Optional[int] = None
    rep_count: int = 0
    duration_seconds: float = 0.0
    form_quality_score: float = 0.0  # 0-100
    anomalies: List[str] = None


@dataclass
class ActionSequence:
    """Sequence of actions in video"""

    actions: List[DetectedAction]
    total_duration: float
    total_reps: int
    avg_form_quality: float
    transitions: List[Tuple[ExerciseType, ExerciseType]]


class MovementFeatureExtractor:
    """Extract features for action recognition"""

    @staticmethod
    def extract_joint_angles(
        keypoints: Dict[str, Dict[str, float]],
    ) -> Dict[str, float]:
        """Extract key joint angles"""
        angles = {}

        # Knee angle
        if all(k in keypoints for k in ["left_hip", "left_knee", "left_ankle"]):
            angles["left_knee"] = MovementFeatureExtractor._angle_between_points(
                keypoints["left_hip"], keypoints["left_knee"], keypoints["left_ankle"]
            )

        if all(k in keypoints for k in ["right_hip", "right_knee", "right_ankle"]):
            angles["right_knee"] = MovementFeatureExtractor._angle_between_points(
                keypoints["right_hip"],
                keypoints["right_knee"],
                keypoints["right_ankle"],
            )

        # Hip angle
        if all(k in keypoints for k in ["left_shoulder", "left_hip", "left_knee"]):
            angles["left_hip"] = MovementFeatureExtractor._angle_between_points(
                keypoints["left_shoulder"],
                keypoints["left_hip"],
                keypoints["left_knee"],
            )

        # Elbow angle
        if all(k in keypoints for k in ["left_shoulder", "left_elbow", "left_wrist"]):
            angles["left_elbow"] = MovementFeatureExtractor._angle_between_points(
                keypoints["left_shoulder"],
                keypoints["left_elbow"],
                keypoints["left_wrist"],
            )

        # Similar for right side
        if all(k in keypoints for k in ["right_shoulder", "right_hip", "right_knee"]):
            angles["right_hip"] = MovementFeatureExtractor._angle_between_points(
                keypoints["right_shoulder"],
                keypoints["right_hip"],
                keypoints["right_knee"],
            )

        if all(k in keypoints for k in ["right_shoulder", "right_elbow", "right_wrist"]):
            angles["right_elbow"] = MovementFeatureExtractor._angle_between_points(
                keypoints["right_shoulder"],
                keypoints["right_elbow"],
                keypoints["right_wrist"],
            )

        return angles

    @staticmethod
    def _angle_between_points(p1, p2, p3):
        """Calculate angle at p2"""
        v1 = np.array([p1["x"] - p2["x"], p1["y"] - p2["y"]])
        v2 = np.array([p3["x"] - p2["x"], p3["y"] - p2["y"]])

        cos_angle = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2) + 1e-6)
        angle = np.degrees(np.arccos(np.clip(cos_angle, -1, 1)))

        return angle

    @staticmethod
    def extract_body_position(
        keypoints: Dict[str, Dict[str, float]],
    ) -> Dict[str, float]:
        """Extract body position features"""
        features = {}

        # Vertical position of key points
        if "left_ankle" in keypoints:
            features["ankle_y"] = keypoints["left_ankle"]["y"]

        if "left_hip" in keypoints:
            features["hip_y"] = keypoints["left_hip"]["y"]

        if "left_shoulder" in keypoints:
            features["shoulder_y"] = keypoints["left_shoulder"]["y"]

        # Lateral spread (width)
        if "left_shoulder" in keypoints and "right_shoulder" in keypoints:
            features["shoulder_width"] = abs(keypoints["right_shoulder"]["x"] - keypoints["left_shoulder"]["x"])

        # Torso angle
        if all(k in keypoints for k in ["left_shoulder", "left_hip"]):
            shoulder_y = keypoints["left_shoulder"]["y"]
            hip_y = keypoints["left_hip"]["y"]
            vertical_dist = abs(shoulder_y - hip_y)
            features["torso_vertical_ratio"] = vertical_dist

        return features

    @staticmethod
    def extract_motion_features(
        keypoints_history: List[Dict[str, Dict[str, float]]],
    ) -> Dict[str, float]:
        """Extract motion/velocity features"""
        if len(keypoints_history) < 2:
            return {}

        features = {}

        # Calculate velocity of key joints
        prev_keypoints = keypoints_history[-2]
        curr_keypoints = keypoints_history[-1]

        # Knee velocity
        if "left_knee" in prev_keypoints and "left_knee" in curr_keypoints:
            knee_x_vel = curr_keypoints["left_knee"]["x"] - prev_keypoints["left_knee"]["x"]
            knee_y_vel = curr_keypoints["left_knee"]["y"] - prev_keypoints["left_knee"]["y"]
            features["knee_velocity"] = np.sqrt(knee_x_vel**2 + knee_y_vel**2)

        # Hip velocity
        if "left_hip" in prev_keypoints and "left_hip" in curr_keypoints:
            hip_x_vel = curr_keypoints["left_hip"]["x"] - prev_keypoints["left_hip"]["x"]
            hip_y_vel = curr_keypoints["left_hip"]["y"] - prev_keypoints["left_hip"]["y"]
            features["hip_velocity"] = np.sqrt(hip_x_vel**2 + hip_y_vel**2)

        # Acceleration (change in velocity)
        if len(keypoints_history) >= 3:
            prev2_keypoints = keypoints_history[-3]
            if "left_knee" in prev2_keypoints and "left_knee" in prev_keypoints:
                prev_vel = np.sqrt(
                    (prev_keypoints["left_knee"]["x"] - prev2_keypoints["left_knee"]["x"]) ** 2
                    + (prev_keypoints["left_knee"]["y"] - prev2_keypoints["left_knee"]["y"]) ** 2
                )
                curr_vel = features.get("knee_velocity", 0)
                features["knee_acceleration"] = curr_vel - prev_vel

        return features


class ActionClassifier:
    """Classify movements and exercises"""

    def __init__(self):
        self.exercise_signatures = self._build_exercise_signatures()
        self.keypoint_history = []
        self.max_history = 60  # Keep 2 seconds at 30fps

    def _build_exercise_signatures(self) -> Dict[ExerciseType, Dict]:
        """Define characteristic angles for each exercise"""
        return {
            ExerciseType.SQUAT: {
                "angle_ranges": {
                    "knee": (60, 120),  # Degrees
                    "hip": (50, 100),
                    "ankle": (80, 110),
                },
                "characteristics": {
                    "high_hip_drop": True,
                    "symmetric": True,
                    "vertical_motion": True,
                },
                "expected_duration": (1.0, 3.0),  # seconds per rep
            },
            ExerciseType.DEADLIFT: {
                "angle_ranges": {
                    "knee": (30, 90),
                    "hip": (40, 90),
                    "ankle": (85, 100),
                },
                "characteristics": {
                    "hip_extension": True,
                    "back_straight": True,
                    "vertical_motion": True,
                },
                "expected_duration": (1.5, 3.5),
            },
            ExerciseType.BENCH_PRESS: {
                "angle_ranges": {
                    "elbow": (60, 140),
                    "shoulder": (45, 120),
                },
                "characteristics": {
                    "horizontal_motion": True,
                    "symmetric": True,
                    "upper_body_focus": True,
                },
                "expected_duration": (1.0, 2.5),
            },
            ExerciseType.RUNNING: {
                "angle_ranges": {
                    "knee": (45, 130),
                },
                "characteristics": {
                    "continuous_motion": True,
                    "alternating_legs": True,
                    "hip_velocity_high": True,
                },
                "expected_duration": (0.3, 1.0),  # Per step
            },
            ExerciseType.STANDING: {
                "angle_ranges": {
                    "knee": (160, 180),
                    "hip": (170, 180),
                },
                "characteristics": {
                    "static": True,
                    "low_motion": True,
                },
                "expected_duration": (1.0, float("inf")),
            },
            ExerciseType.WALKING: {
                "angle_ranges": {
                    "knee": (120, 180),
                    "hip": (160, 180),
                },
                "characteristics": {
                    "continuous_motion": True,
                    "alternating_legs": True,
                    "hip_velocity_moderate": True,
                },
                "expected_duration": (0.5, 2.0),  # Per step
            },
        }

    def classify_action(self, keypoints: Dict[str, Dict[str, float]]) -> Tuple[ExerciseType, float]:
        """
        Classify current action

        Args:
            keypoints: Current keypoints

        Returns:
            Tuple of (ExerciseType, confidence)
        """
        # Add to history
        self.keypoint_history.append(keypoints)
        if len(self.keypoint_history) > self.max_history:
            self.keypoint_history.pop(0)

        try:
            # Extract features
            angles = MovementFeatureExtractor.extract_joint_angles(keypoints)
            body_pos = MovementFeatureExtractor.extract_body_position(keypoints)
            motion = MovementFeatureExtractor.extract_motion_features(
                self.keypoint_history[-5:] if len(self.keypoint_history) >= 5 else self.keypoint_history
            )

            # Score each exercise type
            scores = {}
            for exercise_type, signature in self.exercise_signatures.items():
                score = self._score_exercise(angles, body_pos, motion, signature)
                scores[exercise_type] = score

            # Find best match
            best_exercise = max(scores, key=scores.get)
            best_score = scores[best_exercise]

            # Threshold for "unknown"
            if best_score < 0.3:
                return ExerciseType.UNKNOWN, best_score

            return best_exercise, min(best_score, 1.0)
        except Exception as e:
            logger.error(f"Classification error: {e}")
            return ExerciseType.UNKNOWN, 0.0

    def _score_exercise(
        self,
        angles: Dict[str, float],
        body_pos: Dict[str, float],
        motion: Dict[str, float],
        signature: Dict,
    ) -> float:
        """Score how well data matches exercise signature"""
        score = 0
        weight_sum = 0

        # Check angle ranges
        angle_ranges = signature.get("angle_ranges", {})
        for joint, (min_angle, max_angle) in angle_ranges.items():
            if joint in angles:
                angle = angles[joint]
                if min_angle <= angle <= max_angle:
                    # Perfect fit
                    angle_score = 1.0
                else:
                    # Penalize deviation
                    if angle < min_angle:
                        deviation = min_angle - angle
                    else:
                        deviation = angle - max_angle
                    angle_score = max(0, 1 - (deviation / 45))

                score += angle_score * 0.7
                weight_sum += 0.7

        # Check characteristics
        characteristics = signature.get("characteristics", {})

        if characteristics.get("static") and motion.get("knee_velocity", 0) < 0.01:
            score += 1.0 * 0.3
            weight_sum += 0.3

        if characteristics.get("continuous_motion") and motion.get("knee_velocity", 0) > 0.05:
            score += 1.0 * 0.2
            weight_sum += 0.2

        if weight_sum > 0:
            return score / weight_sum

        return 0.0

    def detect_phase(self, angles: Dict[str, float], motion: Dict[str, float]) -> MovementPhase:
        """Detect current phase of movement"""
        # Simplified phase detection
        velocity = motion.get("knee_velocity", 0)
        acceleration = motion.get("knee_acceleration", 0)

        if velocity < 0.01:
            return MovementPhase.REST
        elif acceleration > 0:
            return MovementPhase.CONCENTRIC
        elif acceleration < -0.01:
            return MovementPhase.ECCENTRIC
        else:
            return MovementPhase.ISOMETRIC


class RepetitionCounter:
    """Count repetitions of exercises"""

    def __init__(self):
        self.rep_count = 0
        self.angle_history = []
        self.in_rep = False
        self.rep_threshold = 15  # Degrees of change

    def update(self, primary_angle: float) -> int:
        """
        Update with new angle measurement

        Args:
            primary_angle: Primary joint angle for exercise

        Returns:
            Updated rep count
        """
        self.angle_history.append(primary_angle)

        # Keep recent history
        if len(self.angle_history) > 60:
            self.angle_history.pop(0)

        if len(self.angle_history) < 10:
            return self.rep_count

        # Detect rep cycle (valley/peak detection)
        recent_angles = self.angle_history[-10:]

        if not self.in_rep:
            # Look for start of rep (significant change)
            if abs(recent_angles[-1] - recent_angles[0]) > self.rep_threshold:
                self.in_rep = True
        else:
            # Look for return to start position
            if abs(recent_angles[-1] - self.angle_history[0]) < self.rep_threshold / 2:
                self.rep_count += 1
                self.in_rep = False

        return self.rep_count


class FormQualityAssessor:
    """Assess exercise form quality"""

    def __init__(self):
        self.anomalies = []

    def assess_squat_form(self, angles: Dict[str, float]) -> Tuple[float, List[str]]:
        """Assess squat form quality"""
        score = 100
        issues = []

        # Check knee alignment
        left_knee = angles.get("left_knee", 90)
        right_knee = angles.get("right_knee", 90)

        if abs(left_knee - right_knee) > 15:
            score -= 20
            issues.append("Asymmetrical knee angles - uneven loading")

        # Check depth
        if left_knee > 110 or right_knee > 110:
            score -= 10
            issues.append("Insufficient squat depth")

        # Check knees over toes
        left_hip = angles.get("left_hip", 80)
        if left_knee > left_hip + 20:
            score -= 15
            issues.append("Knees extending beyond hips - improper form")

        return float(np.clip(score, 0, 100)), issues

    def assess_deadlift_form(self, angles: Dict[str, float]) -> Tuple[float, List[str]]:
        """Assess deadlift form quality"""
        score = 100
        issues = []

        # Check back angle (should be relatively straight)
        # In real implementation, would use spinal angle from keypoints

        # Check hip height
        hip_angle = angles.get("left_hip", 85)
        if hip_angle < 60:
            score -= 25
            issues.append("Hips too low - power loss")
        elif hip_angle > 100:
            score -= 20
            issues.append("Hips too high - excessive strain on back")

        return float(np.clip(score, 0, 100)), issues


if __name__ == "__main__":
    # Example usage
    classifier = ActionClassifier()
    counter = RepetitionCounter()
    assessor = FormQualityAssessor()

    # Simulate keypoints
    sample_keypoints = {
        "left_hip": {"x": 0.4, "y": 0.5},
        "left_knee": {"x": 0.42, "y": 0.7},
        "left_ankle": {"x": 0.4, "y": 0.9},
        "right_hip": {"x": 0.6, "y": 0.5},
        "right_knee": {"x": 0.58, "y": 0.7},
        "right_ankle": {"x": 0.6, "y": 0.9},
    }

    action_type, confidence = classifier.classify_action(sample_keypoints)
    print(f"Action: {action_type.value} ({confidence:.2%})")

    reps = counter.update(90)
    print(f"Reps: {reps}")
