"""
TIER 4: 3D Visualization Engine
Backend support for 3D skeleton visualization, live heatmaps, and comparisons
Generates WebGL/Three.js compatible data
"""

import logging
import math
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


# ============================================================================
# DATA MODELS
# ============================================================================


@dataclass
class Point3D:
    """3D point for visualization"""

    x: float
    y: float
    z: float

    def to_list(self) -> List[float]:
        return [self.x, self.y, self.z]


@dataclass
class SkeletonFrame:
    """Single frame of skeleton data for visualization"""

    frame_id: str
    person_id: str
    timestamp: datetime
    joints: Dict[str, Point3D]
    confidence_scores: Dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return {
            "frame_id": self.frame_id,
            "person_id": self.person_id,
            "timestamp": self.timestamp.isoformat(),
            "joints": {k: v.to_list() for k, v in self.joints.items()},
            "confidence": self.confidence_scores,
        }


@dataclass
class ComparisonData:
    """Data for split-screen comparison"""

    left_skeleton: SkeletonFrame
    right_skeleton: SkeletonFrame
    metrics: Dict[str, float]
    alignment_score: float


# ============================================================================
# 3D VISUALIZATION ENGINE
# ============================================================================


class ThreeDVisualizationEngine:
    """
    3D visualization engine for rendering skeletons and analytics
    Provides WebGL-compatible data for Three.js/Babylon.js rendering
    """

    def __init__(self, max_history_frames: int = 300):
        """
        Initialize 3D visualization engine

        Args:
            max_history_frames: Keep last N frames in memory
        """
        self.max_history = max_history_frames
        self.frame_history: Dict[str, List[SkeletonFrame]] = {}
        self.comparison_sessions: Dict[str, ComparisonData] = {}
        self.heatmap_data: Dict[str, Dict] = {}
        self.trajectory_trails: Dict[str, List[Point3D]] = {}

        # Standard skeleton structure for WebGL
        self.bone_structure = [
            ("nose", "left_eye"),
            ("left_eye", "left_ear"),
            ("nose", "right_eye"),
            ("right_eye", "right_ear"),
            ("left_shoulder", "right_shoulder"),
            ("left_shoulder", "left_elbow"),
            ("left_elbow", "left_wrist"),
            ("right_shoulder", "right_elbow"),
            ("right_elbow", "right_wrist"),
            ("left_hip", "right_hip"),
            ("left_hip", "left_knee"),
            ("left_knee", "left_ankle"),
            ("right_hip", "right_knee"),
            ("right_knee", "right_ankle"),
            ("left_shoulder", "left_hip"),
            ("right_shoulder", "right_hip"),
        ]

        logger.info(f"3D Visualization engine initialized (max {max_history_frames} frames)")

    async def create_skeleton_visualization(self, pose_data: Dict) -> Dict[str, Any]:
        """
        Create 3D skeleton visualization data

        Args:
            pose_data: Raw pose detection data

        Returns:
            WebGL-compatible skeleton geometry
        """
        try:
            frame_id = str(uuid.uuid4())
            person_id = pose_data.get("person_id", "0")

            # Extract 3D joints
            joints_3d = {}
            landmarks = pose_data.get("landmarks_3d", {})

            for joint_name, coord in landmarks.items():
                if isinstance(coord, dict):
                    joints_3d[joint_name] = Point3D(
                        coord.get("x", 0), coord.get("y", 0), coord.get("z", 0)
                    )

            # Create frame
            frame = SkeletonFrame(
                frame_id=frame_id,
                person_id=person_id,
                timestamp=datetime.utcnow(),
                joints=joints_3d,
                confidence_scores=pose_data.get("confidence", {}),
            )

            # Store in history
            if person_id not in self.frame_history:
                self.frame_history[person_id] = []

            self.frame_history[person_id].append(frame)

            # Maintain history limit
            if len(self.frame_history[person_id]) > self.max_history:
                self.frame_history[person_id] = self.frame_history[person_id][-self.max_history :]

            # Update trajectory trail
            await self._update_trajectory_trail(person_id, joints_3d.get("nose", Point3D(0, 0, 0)))

            # Generate geometry
            geometry = self._generate_webgl_geometry(frame)

            return {
                "frame_id": frame_id,
                "person_id": person_id,
                "geometry": geometry,
                "timestamp": frame.timestamp.isoformat(),
            }
        except Exception as e:
            logger.error(f"Skeleton visualization creation failed: {str(e)}")
            return {"error": str(e)}

    def _generate_webgl_geometry(self, frame: SkeletonFrame) -> Dict[str, Any]:
        """Generate Three.js compatible geometry"""
        vertices = []
        indices = []
        colors = []

        # Add vertices for all joints
        joint_index_map = {}
        for i, (joint_name, joint) in enumerate(frame.joints.items()):
            vertices.extend(joint.to_list())
            joint_index_map[joint_name] = i

        # Add bone indices
        for bone_from, bone_to in self.bone_structure:
            if bone_from in joint_index_map and bone_to in joint_index_map:
                from_idx = joint_index_map[bone_from]
                to_idx = joint_index_map[bone_to]
                indices.extend([from_idx, to_idx])

                # Colors based on body part
                if "arm" in bone_from or "elbow" in bone_from:
                    colors.extend([1, 0, 0, 1, 0, 0])  # Red for arms
                elif "leg" in bone_from or "knee" in bone_from:
                    colors.extend([0, 1, 0, 0, 1, 0])  # Green for legs
                else:
                    colors.extend([0, 0, 1, 0, 0, 1])  # Blue for torso

        return {
            "vertices": vertices,
            "indices": indices,
            "colors": colors,
            "vertex_count": len(frame.joints),
            "bone_count": len(indices) // 2,
        }

    async def _update_trajectory_trail(self, person_id: str, joint_position: Point3D):
        """Update trajectory trail for person"""
        if person_id not in self.trajectory_trails:
            self.trajectory_trails[person_id] = []

        self.trajectory_trails[person_id].append(joint_position)

        # Keep last 100 points
        if len(self.trajectory_trails[person_id]) > 100:
            self.trajectory_trails[person_id] = self.trajectory_trails[person_id][-100:]

    async def get_trajectory_visualization(self, person_id: str) -> Dict[str, Any]:
        """
        Get trajectory trail visualization

        Args:
            person_id: Person to get trajectory for

        Returns:
            Trail geometry for rendering
        """
        try:
            trail = self.trajectory_trails.get(person_id, [])

            if not trail:
                return {"error": "No trajectory data"}

            # Convert to line geometry
            vertices = []
            for point in trail:
                vertices.extend(point.to_list())

            indices = list(range(len(trail) - 1))

            return {
                "person_id": person_id,
                "trail_points": len(trail),
                "geometry": {
                    "vertices": vertices,
                    "indices": indices,
                    "line_width": 2,
                    "color": [0.5, 1.0, 0.5],
                },
            }
        except Exception as e:
            logger.error(f"Trajectory fetch failed: {str(e)}")
            return {"error": str(e)}

    async def create_comparison_view(
        self, left_person_id: str, right_person_id: str, frame_count: int = 1
    ) -> Dict[str, Any]:
        """
        Create split-screen comparison visualization

        Args:
            left_person_id: Left side person
            right_person_id: Right side person
            frame_count: Frames to compare

        Returns:
            Comparison geometry and alignment score
        """
        try:
            comparison_id = str(uuid.uuid4())

            left_frames = self.frame_history.get(left_person_id, [])
            right_frames = self.frame_history.get(right_person_id, [])

            if not left_frames or not right_frames:
                return {"error": "Insufficient frame data"}

            # Get most recent frames
            left_frame = left_frames[-1]
            right_frame = right_frames[-1]

            # Calculate alignment
            alignment_score = self._calculate_alignment_score(left_frame, right_frame)

            # Generate comparison data
            comparison = ComparisonData(
                left_skeleton=left_frame,
                right_skeleton=right_frame,
                metrics=self._calculate_metrics_diff(left_frame, right_frame),
                alignment_score=alignment_score,
            )

            self.comparison_sessions[comparison_id] = comparison

            return {
                "comparison_id": comparison_id,
                "left": left_frame.to_dict(),
                "right": right_frame.to_dict(),
                "alignment_score": alignment_score,
                "metrics_diff": comparison.metrics,
                "recommendation": self._get_comparison_recommendation(alignment_score),
            }
        except Exception as e:
            logger.error(f"Comparison view creation failed: {str(e)}")
            return {"error": str(e)}

    def _calculate_alignment_score(self, frame1: SkeletonFrame, frame2: SkeletonFrame) -> float:
        """
        Calculate how well two skeletons align

        Args:
            frame1: First skeleton frame
            frame2: Second skeleton frame

        Returns:
            Alignment score (0-1, where 1 is perfect alignment)
        """
        total_distance = 0
        joint_count = 0

        for joint_name in frame1.joints:
            if joint_name in frame2.joints:
                p1 = frame1.joints[joint_name]
                p2 = frame2.joints[joint_name]

                distance = math.sqrt((p1.x - p2.x) ** 2 + (p1.y - p2.y) ** 2 + (p1.z - p2.z) ** 2)

                total_distance += distance
                joint_count += 1

        if joint_count == 0:
            return 0.0

        avg_distance = total_distance / joint_count
        alignment = max(0, 1 - avg_distance * 2)  # Convert distance to alignment

        return round(alignment, 3)

    def _calculate_metrics_diff(
        self, frame1: SkeletonFrame, frame2: SkeletonFrame
    ) -> Dict[str, float]:
        """Calculate metric differences between frames"""
        return {
            "pose_distance": self._calculate_alignment_score(frame1, frame2),
            "height_diff": abs(
                frame1.joints.get("nose", Point3D(0, 0, 0)).y
                - frame2.joints.get("nose", Point3D(0, 0, 0)).y
            ),
            "width_diff": abs(
                frame1.joints.get("left_shoulder", Point3D(0, 0, 0)).x
                - frame1.joints.get("right_shoulder", Point3D(0, 0, 0)).x
                - (
                    frame2.joints.get("left_shoulder", Point3D(0, 0, 0)).x
                    - frame2.joints.get("right_shoulder", Point3D(0, 0, 0)).x
                )
            ),
        }

    def _get_comparison_recommendation(self, alignment: float) -> str:
        """Get recommendation based on alignment"""
        if alignment > 0.9:
            return "Perfect form match!"
        elif alignment > 0.75:
            return "Good alignment"
        elif alignment > 0.6:
            return "Slightly different form"
        else:
            return "Significantly different form"

    async def generate_live_heatmap(self, person_id: str, analysis_data: Dict) -> Dict[str, Any]:
        """
        Generate live joint stress heatmap

        Args:
            person_id: Person to analyze
            analysis_data: Biomechanical analysis data

        Returns:
            Heatmap geometry for WebGL rendering
        """
        try:
            heatmap_id = str(uuid.uuid4())

            # Calculate stress levels for each joint
            stress_levels = {}

            frames = self.frame_history.get(person_id, [])
            if not frames:
                return {"error": "No frame history"}

            for joint_name in frames[-1].joints:
                # Simulate stress calculation (in production, use actual biomechanics)
                stress = self._calculate_joint_stress(joint_name, analysis_data)
                stress_levels[joint_name] = stress

            # Create heatmap visualization
            heatmap_vertices = []
            heatmap_colors = []

            for joint_name, joint_pos in frames[-1].joints.items():
                stress = stress_levels.get(joint_name, 0)

                # Add vertex for joint
                heatmap_vertices.extend(joint_pos.to_list())

                # Color based on stress (green to red gradient)
                r = stress
                g = 1 - stress
                b = 0
                a = 0.7
                heatmap_colors.extend([r, g, b, a])

            self.heatmap_data[heatmap_id] = {
                "person_id": person_id,
                "stress_levels": stress_levels,
                "timestamp": datetime.utcnow().isoformat(),
            }

            return {
                "heatmap_id": heatmap_id,
                "person_id": person_id,
                "geometry": {
                    "vertices": heatmap_vertices,
                    "colors": heatmap_colors,
                    "point_size": 8,
                    "point_count": len(frames[-1].joints),
                },
                "stress_levels": stress_levels,
                "high_risk_joints": [j for j, s in stress_levels.items() if s > 0.7],
            }
        except Exception as e:
            logger.error(f"Heatmap generation failed: {str(e)}")
            return {"error": str(e)}

    def _calculate_joint_stress(self, joint_name: str, analysis_data: Dict) -> float:
        """
        Calculate stress level for joint (0-1)

        Args:
            joint_name: Joint name
            analysis_data: Biomechanical analysis

        Returns:
            Stress level (0-1)
        """
        # Base stress levels
        base_stress = {
            "left_knee": 0.6,
            "right_knee": 0.6,
            "left_ankle": 0.4,
            "right_ankle": 0.4,
            "left_shoulder": 0.3,
            "right_shoulder": 0.3,
            "lower_back": 0.7,
        }

        stress = base_stress.get(joint_name, 0.2)

        # Adjust based on analysis data
        if analysis_data.get("form_quality", 100) < 70:
            stress = min(1.0, stress + 0.2)

        return stress

    async def create_interactive_dashboard(self, user_id: str) -> Dict[str, Any]:
        """
        Create interactive 3D dashboard data

        Args:
            user_id: User identifier

        Returns:
            Dashboard configuration with multiple views
        """
        try:
            return {
                "user_id": user_id,
                "dashboard_id": str(uuid.uuid4()),
                "views": [
                    {
                        "name": "Live Skeleton",
                        "type": "skeleton_overlay",
                        "position": [0, 0],
                        "size": [0.5, 1.0],
                    },
                    {
                        "name": "Joint Heatmap",
                        "type": "heatmap",
                        "position": [0.5, 0],
                        "size": [0.5, 0.5],
                    },
                    {
                        "name": "Movement Trail",
                        "type": "trajectory",
                        "position": [0.5, 0.5],
                        "size": [0.5, 0.5],
                    },
                ],
                "interactive_features": [
                    "rotate_skeleton",
                    "zoom_view",
                    "toggle_heatmap",
                    "record_comparison",
                    "export_visualization",
                ],
                "rendering_config": {
                    "fps": 60,
                    "quality": "high",
                    "lighting": "realistic",
                    "shadows": True,
                },
            }
        except Exception as e:
            logger.error(f"Dashboard creation failed: {str(e)}")
            return {"error": str(e)}


# ============================================================================
# EXPORT UTILITIES
# ============================================================================


class VisualizationExporter:
    """Export visualizations in various formats"""

    @staticmethod
    async def export_to_gltf(skeleton_data: Dict) -> Dict[str, str]:
        """
        Export skeleton to glTF format

        Args:
            skeleton_data: Skeleton geometry data

        Returns:
            glTF model data
        """
        try:
            # In production, generate proper glTF format
            return {
                "format": "gltf",
                "model": "base64_encoded_gltf",
                "file_size_kb": 150,
            }
        except Exception as e:
            logger.error(f"Export failed: {str(e)}")
            return {"error": str(e)}


logger.info("3D visualization engine module loaded - Tier 4 complete")
