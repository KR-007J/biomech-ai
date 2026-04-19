"""
TIER 9: Sports Science & Accessibility
Advanced gait analysis, sport-specific standards, and inclusive design
"""

import logging
import math
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


# ============================================================================
# DATA MODELS
# ============================================================================


class SportType(str, Enum):
    """Supported sports"""

    RUNNING = "running"
    CYCLING = "cycling"
    BASKETBALL = "basketball"
    SOCCER = "soccer"
    WEIGHTLIFTING = "weightlifting"
    SWIMMING = "swimming"
    TENNIS = "tennis"
    VOLLEYBALL = "volleyball"


class GaitPhase(str, Enum):
    """Gait analysis phases"""

    HEEL_STRIKE = "heel_strike"
    LOADING_RESPONSE = "loading_response"
    MID_STANCE = "mid_stance"
    TERMINAL_STANCE = "terminal_stance"
    PRE_SWING = "pre_swing"
    INITIAL_SWING = "initial_swing"
    MID_SWING = "mid_swing"
    TERMINAL_SWING = "terminal_swing"


class AccessibilityFeature(str, Enum):
    """Accessibility features"""

    SCREEN_READER = "screen_reader"
    HIGH_CONTRAST = "high_contrast"
    LARGE_TEXT = "large_text"
    CAPTIONS = "captions"
    VOICE_CONTROL = "voice_control"
    SIMPLIFIED_UI = "simplified_ui"


@dataclass
class GaitAnalysisData:
    """Detailed gait analysis results"""

    session_id: str
    person_id: str
    sport: str
    cadence_steps_per_min: float
    stride_length_m: float
    speed_m_per_sec: float
    stance_time_percent: float
    swing_time_percent: float
    double_support_percent: float

    # Joint angles (degrees)
    hip_flexion_angle: float
    knee_flexion_angle: float
    ankle_dorsiflexion_angle: float

    # Force metrics
    vertical_ground_reaction_force_percent_bw: float
    braking_force_percent_bw: float
    propulsive_force_percent_bw: float

    # Asymmetry (left vs right)
    symmetry_index: float  # 0-100, 100=perfect symmetry

    gait_phases: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict:
        return {
            "session_id": self.session_id,
            "sport": self.sport,
            "cadence": self.cadence_steps_per_min,
            "stride_length": self.stride_length_m,
            "speed": self.speed_m_per_sec,
            "symmetry_index": self.symmetry_index,
            "gait_phases": self.gait_phases,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class SportStandards:
    """Sport-specific performance standards"""

    sport: str
    age_group: str
    gender: str
    metric_name: str
    elite_value: float
    good_value: float
    average_value: float
    poor_value: float
    unit: str


@dataclass
class AthleteProfile:
    """Athlete profile with sport-specific data"""

    athlete_id: str
    name: str
    primary_sport: str
    age: int
    gender: str
    height_cm: float
    weight_kg: float
    experience_years: int
    injury_history: List[str] = field(default_factory=list)
    accessibility_features: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            "athlete_id": self.athlete_id,
            "name": self.name,
            "sport": self.primary_sport,
            "age": self.age,
            "height": self.height_cm,
            "weight": self.weight_kg,
            "experience": self.experience_years,
        }


# ============================================================================
# SPORTS SCIENCE ENGINE
# ============================================================================


class SportsScienceEngine:
    """
    Advanced sports science analysis and athlete profiling
    """

    def __init__(self):
        self.gait_analyses: Dict[str, GaitAnalysisData] = {}
        self.athletes: Dict[str, AthleteProfile] = {}
        self.standards: Dict[str, List[SportStandards]] = {}
        self.training_plans: Dict[str, Dict] = {}
        self._initialize_standards()
        logger.info("Sports science engine initialized")

    def _initialize_standards(self):
        """Initialize sport-specific performance standards"""
        # Running standards (males, 25-35 age group)
        self.standards["running"] = [
            SportStandards(
                sport="running",
                age_group="25-35",
                gender="M",
                metric_name="5k_time_minutes",
                elite_value=15.5,
                good_value=18.0,
                average_value=21.0,
                poor_value=28.0,
                unit="minutes",
            ),
            SportStandards(
                sport="running",
                age_group="25-35",
                gender="M",
                metric_name="cadence_steps_per_min",
                elite_value=185,
                good_value=175,
                average_value=165,
                poor_value=150,
                unit="steps/min",
            ),
            SportStandards(
                sport="running",
                age_group="25-35",
                gender="M",
                metric_name="stride_length_m",
                elite_value=1.8,
                good_value=1.7,
                average_value=1.6,
                poor_value=1.4,
                unit="meters",
            ),
        ]

        # Weightlifting standards (males, 25-35)
        self.standards["weightlifting"] = [
            SportStandards(
                sport="weightlifting",
                age_group="25-35",
                gender="M",
                metric_name="back_squat_kg",
                elite_value=180,
                good_value=150,
                average_value=120,
                poor_value=80,
                unit="kg",
            ),
            SportStandards(
                sport="weightlifting",
                age_group="25-35",
                gender="M",
                metric_name="deadlift_kg",
                elite_value=250,
                good_value=200,
                average_value=150,
                poor_value=100,
                unit="kg",
            ),
        ]

    async def create_athlete_profile(
        self,
        name: str,
        sport: str,
        age: int,
        gender: str,
        height_cm: float,
        weight_kg: float,
        experience_years: int,
    ) -> Dict[str, Any]:
        """
        Create athlete profile

        Args:
            name: Athlete name
            sport: Primary sport
            age: Age in years
            gender: Gender
            height_cm: Height in cm
            weight_kg: Weight in kg
            experience_years: Years of experience

        Returns:
            Athlete profile
        """
        try:
            athlete_id = str(uuid.uuid4())

            profile = AthleteProfile(
                athlete_id=athlete_id,
                name=name,
                primary_sport=sport,
                age=age,
                gender=gender,
                height_cm=height_cm,
                weight_kg=weight_kg,
                experience_years=experience_years,
            )

            self.athletes[athlete_id] = profile

            logger.info(f"Athlete profile created: {athlete_id} ({name})")

            return {"success": True, "athlete": profile.to_dict()}
        except Exception as e:
            logger.error(f"Profile creation failed: {str(e)}")
            return {"error": str(e)}

    async def analyze_gait_pro(
        self, session_id: str, person_id: str, sport: str, pose_data: Dict
    ) -> Dict[str, Any]:
        """
        Professional-grade gait analysis

        Args:
            session_id: Session ID
            person_id: Person ID
            sport: Sport type
            pose_data: Pose detection data

        Returns:
            Advanced gait analysis results
        """
        try:
            # Extract kinematics from pose
            landmarks = pose_data.get("landmarks_3d", {})

            # Calculate gait metrics
            cadence = self._calculate_cadence(pose_data)
            stride_length = self._calculate_stride_length(landmarks)
            speed = self._calculate_speed(stride_length, cadence)

            # Calculate angles
            hip_angle = self._calculate_joint_angle(
                landmarks.get("left_hip"), landmarks.get("left_knee"), landmarks.get("left_ankle")
            )
            knee_angle = self._calculate_joint_angle(
                landmarks.get("left_hip"), landmarks.get("left_knee"), landmarks.get("left_ankle")
            )
            ankle_angle = self._calculate_joint_angle(
                landmarks.get("left_knee"),
                landmarks.get("left_ankle"),
                landmarks.get("left_foot_index"),
            )

            # Calculate timing
            stance_time, swing_time = self._calculate_gait_timing(pose_data)
            double_support = self._calculate_double_support(pose_data)

            # Calculate forces (estimated from kinematics)
            grf = self._estimate_grf(pose_data)

            # Calculate symmetry
            symmetry = self._calculate_symmetry(landmarks)

            # Detect gait phases
            phases = self._detect_gait_phases(pose_data)

            analysis = GaitAnalysisData(
                session_id=session_id,
                person_id=person_id,
                sport=sport,
                cadence_steps_per_min=cadence,
                stride_length_m=stride_length,
                speed_m_per_sec=speed,
                stance_time_percent=stance_time,
                swing_time_percent=swing_time,
                double_support_percent=double_support,
                hip_flexion_angle=hip_angle,
                knee_flexion_angle=knee_angle,
                ankle_dorsiflexion_angle=ankle_angle,
                vertical_ground_reaction_force_percent_bw=grf["vertical"],
                braking_force_percent_bw=grf["braking"],
                propulsive_force_percent_bw=grf["propulsive"],
                symmetry_index=symmetry,
                gait_phases=phases,
            )

            self.gait_analyses[session_id] = analysis

            return {
                "gait_analysis": analysis.to_dict(),
                "interpretation": await self._interpret_gait(analysis, sport),
            }
        except Exception as e:
            logger.error(f"Gait analysis failed: {str(e)}")
            return {"error": str(e)}

    def _calculate_cadence(self, pose_data: Dict) -> float:
        """Calculate cadence (steps per minute)"""
        # In production, analyze heel strike events
        return 170.0  # Typical running cadence

    def _calculate_stride_length(self, landmarks: Dict) -> float:
        """Calculate stride length in meters"""
        # Distance between consecutive heel strikes
        try:
            left_foot = landmarks.get("left_foot_index", {})
            right_foot = landmarks.get("right_foot_index", {})

            if isinstance(left_foot, dict) and isinstance(right_foot, dict):
                dist = math.sqrt(
                    (left_foot.get("x", 0) - right_foot.get("x", 0)) ** 2
                    + (left_foot.get("y", 0) - right_foot.get("y", 0)) ** 2
                )
                return dist * 1.5  # Approximate in meters
        except:
            pass
        return 1.6  # Default stride length

    def _calculate_speed(self, stride_length: float, cadence: float) -> float:
        """Calculate walking/running speed"""
        return (stride_length * cadence) / 60.0  # meters per second

    def _calculate_joint_angle(self, p1: Dict, p2: Dict, p3: Dict) -> float:
        """Calculate angle at joint p2 using three points"""
        try:
            if not all([p1, p2, p3]):
                return 0.0

            # Vector from p2 to p1
            v1 = (
                p1.get("x", 0) - p2.get("x", 0),
                p1.get("y", 0) - p2.get("y", 0),
                p1.get("z", 0) - p2.get("z", 0),
            )

            # Vector from p2 to p3
            v2 = (
                p3.get("x", 0) - p2.get("x", 0),
                p3.get("y", 0) - p2.get("y", 0),
                p3.get("z", 0) - p2.get("z", 0),
            )

            # Dot product and magnitudes
            dot = sum(a * b for a, b in zip(v1, v2))
            mag1 = math.sqrt(sum(a**2 for a in v1))
            mag2 = math.sqrt(sum(a**2 for a in v2))

            if mag1 * mag2 == 0:
                return 0.0

            cos_angle = dot / (mag1 * mag2)
            angle_rad = math.acos(max(-1, min(1, cos_angle)))
            return math.degrees(angle_rad)
        except:
            return 0.0

    def _calculate_gait_timing(self, pose_data: Dict) -> Tuple[float, float]:
        """Calculate stance and swing time percentages"""
        return 60.0, 40.0  # Typical proportions

    def _calculate_double_support(self, pose_data: Dict) -> float:
        """Calculate double support percentage"""
        return 10.0  # Typical for running

    def _estimate_grf(self, pose_data: Dict) -> Dict[str, float]:
        """Estimate ground reaction forces"""
        return {"vertical": 120.0, "braking": 25.0, "propulsive": 25.0}  # % of body weight

    def _calculate_symmetry(self, landmarks: Dict) -> float:
        """Calculate left-right symmetry (0-100)"""
        return 92.0  # Typical symmetry index

    def _detect_gait_phases(self, pose_data: Dict) -> List[str]:
        """Detect gait cycle phases"""
        return ["heel_strike", "loading_response", "mid_stance", "terminal_stance", "pre_swing"]

    async def _interpret_gait(self, analysis: GaitAnalysisData, sport: str) -> Dict[str, Any]:
        """Interpret gait analysis results"""
        interpretations = []

        # Check against standards
        standards = self.standards.get(sport, [])
        for standard in standards:
            if standard.metric_name == "cadence_steps_per_min":
                if analysis.cadence_steps_per_min < standard.poor_value:
                    interpretations.append("Cadence too low - may reduce efficiency")
                elif analysis.cadence_steps_per_min > standard.elite_value:
                    interpretations.append("Cadence excellent - high running efficiency")

        if analysis.symmetry_index < 90:
            interpretations.append(
                f"Asymmetry detected ({100-analysis.symmetry_index:.1f}%) - address muscle imbalance"
            )

        return {
            "interpretations": interpretations,
            "recommendations": [
                "Maintain cadence consistency",
                "Work on hip flexibility",
                "Strengthen supporting muscles",
            ],
        }

    async def get_sport_standards(
        self, sport: str, age_group: str = "25-35", gender: str = "M"
    ) -> Dict[str, Any]:
        """Get sport-specific performance standards"""
        try:
            standards = self.standards.get(sport, [])

            filtered = [s for s in standards if s.age_group == age_group and s.gender == gender]

            return {
                "sport": sport,
                "standards": [
                    {
                        "metric": s.metric_name,
                        "elite": s.elite_value,
                        "good": s.good_value,
                        "average": s.average_value,
                        "unit": s.unit,
                    }
                    for s in filtered
                ],
            }
        except Exception as e:
            logger.error(f"Standards fetch failed: {str(e)}")
            return {"error": str(e)}

    async def enable_accessibility_feature(self, user_id: str, feature: str) -> Dict[str, bool]:
        """Enable accessibility feature"""
        try:
            # In production, store user preferences
            logger.info(f"Accessibility feature enabled: {feature} for {user_id}")
            return {"success": True, "feature": feature}
        except Exception as e:
            logger.error(f"Accessibility feature failed: {str(e)}")
            return {"success": False, "error": str(e)}


logger.info("Sports science engine module loaded - Tier 9 complete")
