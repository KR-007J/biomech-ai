"""
Tier 3: Multi-Person Analysis & Tracking
==========================================

Support for tracking and analyzing multiple people simultaneously:
- Real-time multi-person detection
- Person re-identification across sessions
- Group exercise analysis
- Comparative metrics for teams/classes
- Synchronization analysis
"""

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple

import numpy as np

logger = logging.getLogger(__name__)


class PersonTrackingState(Enum):
    """Person tracking states"""

    DETECTED = "detected"
    TRACKED = "tracked"
    LOST = "lost"
    IDENTIFIED = "identified"


@dataclass
class DetectedPerson:
    """Person detected in frame"""

    person_id: str  # Temporary frame-level ID
    track_id: Optional[str] = None  # Cross-session tracking ID
    keypoints: Dict[str, Dict[str, float]] = field(default_factory=dict)
    bounding_box: Tuple[float, float, float, float] = (0, 0, 1, 1)  # (x1, y1, x2, y2)
    confidence: float = 0.0
    timestamp: datetime = field(default_factory=datetime.utcnow)
    state: PersonTrackingState = PersonTrackingState.DETECTED
    features: Optional[np.ndarray] = None  # For re-identification


@dataclass
class PersonProfile:
    """User profile for person identification"""

    track_id: str
    user_name: Optional[str] = None
    session_count: int = 0
    last_seen: datetime = field(default_factory=datetime.utcnow)
    average_height: float = 0.0
    average_build: str = "average"  # small, average, large
    features_history: List[np.ndarray] = field(default_factory=list)
    identification_confidence: float = 0.0


@dataclass
class GroupSyncMetrics:
    """Synchronization metrics for group exercise"""

    group_id: str
    member_ids: Set[str]
    timestamp: datetime
    movement_sync_score: float  # 0-1: how synchronized are movements
    phase_alignment: float  # % of members in same gait phase
    pace_consistency: float  # 0-1: consistency of cadence
    formation_stability: float  # 0-1: formation cohesion


class MultiPersonTracker:
    """Track multiple people across frames"""

    def __init__(self, max_persons: int = 10, tracking_timeout: float = 2.0):
        """
        Initialize tracker

        Args:
            max_persons: Maximum people to track
            tracking_timeout: Seconds before losing track
        """
        self.max_persons = max_persons
        self.tracking_timeout = tracking_timeout

        self.active_tracks: Dict[str, DetectedPerson] = {}
        self.historical_frames: List[Dict[str, DetectedPerson]] = []
        self.profiles: Dict[str, PersonProfile] = {}

        self.frame_count = 0
        self.last_track_id = 0

    def update(
        self, detected_persons: List[DetectedPerson], frame_timestamp: datetime
    ) -> Dict[str, DetectedPerson]:
        """
        Update tracker with new detections

        Args:
            detected_persons: List of detected people in frame
            frame_timestamp: Frame timestamp

        Returns:
            Tracked persons with consistent IDs
        """
        self.frame_count += 1

        # 1. Data association (match new detections to existing tracks)
        assignments = self._data_association(detected_persons)

        # 2. Update existing tracks
        tracked_persons = {}
        used_detections = set()

        for track_id, det_idx in assignments.items():
            if det_idx is not None:
                detection = detected_persons[det_idx]
                detection.track_id = track_id
                detection.state = PersonTrackingState.TRACKED
                self.active_tracks[track_id] = detection
                tracked_persons[track_id] = detection
                used_detections.add(det_idx)

        # 3. Create new tracks for unassociated detections
        for i, detection in enumerate(detected_persons):
            if i not in used_detections:
                self.last_track_id += 1
                new_track_id = f"track_{self.last_track_id}"
                detection.track_id = new_track_id
                self.active_tracks[new_track_id] = detection
                tracked_persons[new_track_id] = detection

        # 4. Handle lost tracks
        self._handle_lost_tracks(frame_timestamp)

        # 5. Store frame history
        self.historical_frames.append(tracked_persons.copy())
        if len(self.historical_frames) > 300:  # Keep ~10s of 30fps video
            self.historical_frames.pop(0)

        return tracked_persons

    def _data_association(self, detections: List[DetectedPerson]) -> Dict[str, Optional[int]]:
        """
        Associate detections to existing tracks

        Args:
            detections: New detections

        Returns:
            Mapping of track_id to detection index
        """
        assignments = {}

        try:
            from scipy.optimize import linear_sum_assignment

            if not self.active_tracks or not detections:
                return assignments

            # Build cost matrix based on spatial distance and appearance
            n_tracks = len(self.active_tracks)
            n_detections = len(detections)
            cost_matrix = np.full((n_tracks, n_detections), np.inf)

            track_ids = list(self.active_tracks.keys())

            for i, track_id in enumerate(track_ids):
                track = self.active_tracks[track_id]

                for j, detection in enumerate(detections):
                    # Spatial distance (IoU-based)
                    iou = self._compute_iou(track.bounding_box, detection.bounding_box)
                    spatial_cost = 1 - iou

                    # Appearance distance
                    appearance_cost = 0
                    if track.features is not None and detection.features is not None:
                        appearance_cost = np.linalg.norm(track.features - detection.features)
                        appearance_cost = min(appearance_cost, 2.0)  # Cap at 2.0

                    # Combined cost
                    cost_matrix[i, j] = spatial_cost * 0.6 + appearance_cost * 0.4

            # Solve assignment problem
            track_indices, det_indices = linear_sum_assignment(cost_matrix)

            # Filter assignments by cost threshold
            threshold = 0.5
            for t_idx, d_idx in zip(track_indices, det_indices):
                if cost_matrix[t_idx, d_idx] < threshold:
                    assignments[track_ids[t_idx]] = d_idx
                else:
                    assignments[track_ids[t_idx]] = None

            return assignments
        except Exception as e:
            logger.error(f"Data association error: {e}")
            return {}

    def _compute_iou(
        self,
        box1: Tuple[float, float, float, float],
        box2: Tuple[float, float, float, float],
    ) -> float:
        """Compute intersection over union"""
        x1_min, y1_min, x1_max, y1_max = box1
        x2_min, y2_min, x2_max, y2_max = box2

        # Intersection
        inter_x_min = max(x1_min, x2_min)
        inter_y_min = max(y1_min, y2_min)
        inter_x_max = min(x1_max, x2_max)
        inter_y_max = min(y1_max, y2_max)

        inter_area = max(0, inter_x_max - inter_x_min) * max(0, inter_y_max - inter_y_min)

        # Union
        box1_area = (x1_max - x1_min) * (y1_max - y1_min)
        box2_area = (x2_max - x2_min) * (y2_max - y2_min)
        union_area = box1_area + box2_area - inter_area

        return inter_area / union_area if union_area > 0 else 0

    def _handle_lost_tracks(self, current_time: datetime) -> None:
        """Remove tracks that haven't been detected recently"""
        timeout_threshold = timedelta(seconds=self.tracking_timeout)
        lost_tracks = []

        for track_id, person in list(self.active_tracks.items()):
            if current_time - person.timestamp > timeout_threshold:
                person.state = PersonTrackingState.LOST
                lost_tracks.append(track_id)

        for track_id in lost_tracks:
            del self.active_tracks[track_id]
            logger.debug(f"Lost track: {track_id}")

    def get_current_tracks(self) -> List[DetectedPerson]:
        """Get currently active tracks"""
        return list(self.active_tracks.values())

    def get_track_history(self, track_id: str, frames_back: int = 30) -> List[DetectedPerson]:
        """Get historical positions for track"""
        history = []

        for frame_data in self.historical_frames[-frames_back:]:
            if track_id in frame_data:
                history.append(frame_data[track_id])

        return history


class PersonReIdentificationEngine:
    """Re-identify people across sessions"""

    def __init__(self):
        self.profiles: Dict[str, PersonProfile] = {}
        self.feature_storage: Dict[str, List[np.ndarray]] = {}

    def register_person(self, user_name: str, features: np.ndarray) -> str:
        """
        Register new person

        Args:
            user_name: User name
            features: Appearance features

        Returns:
            Track ID for person
        """
        track_id = str(uuid.uuid4())[:8]

        profile = PersonProfile(track_id=track_id, user_name=user_name, features_history=[features])

        self.profiles[track_id] = profile
        self.feature_storage[track_id] = [features]

        logger.info(f"Registered person: {user_name} (ID: {track_id})")
        return track_id

    def identify_person(
        self, features: np.ndarray, confidence_threshold: float = 0.85
    ) -> Tuple[Optional[str], float]:
        """
        Identify person from features

        Args:
            features: Person features
            confidence_threshold: Minimum confidence

        Returns:
            Tuple of (track_id, confidence) or (None, 0)
        """
        best_match = None
        best_confidence = 0

        for track_id, stored_features in self.feature_storage.items():
            # Compute similarity to average stored features
            avg_features = np.mean(stored_features, axis=0)
            similarity = self._compute_similarity(features, avg_features)

            if similarity > best_confidence:
                best_confidence = similarity
                best_match = track_id

        if best_confidence >= confidence_threshold:
            return best_match, best_confidence

        return None, 0

    def update_features(self, track_id: str, features: np.ndarray, max_features: int = 50) -> None:
        """Update feature set for person"""
        if track_id not in self.feature_storage:
            self.feature_storage[track_id] = []

        self.feature_storage[track_id].append(features)

        # Keep recent features only
        if len(self.feature_storage[track_id]) > max_features:
            self.feature_storage[track_id] = self.feature_storage[track_id][-max_features:]

        # Update profile
        if track_id in self.profiles:
            self.profiles[track_id].features_history = self.feature_storage[track_id]
            self.profiles[track_id].last_seen = datetime.utcnow()

    @staticmethod
    def _compute_similarity(f1: np.ndarray, f2: np.ndarray) -> float:
        """Compute cosine similarity"""
        norm1 = np.linalg.norm(f1)
        norm2 = np.linalg.norm(f2)

        if norm1 == 0 or norm2 == 0:
            return 0

        return np.dot(f1, f2) / (norm1 * norm2)


class GroupExerciseAnalyzer:
    """Analyze synchronized group exercises"""

    def __init__(self):
        self.movement_history: Dict[str, List[Dict]] = {}

    def record_group_movement(
        self, group_members: List[DetectedPerson], frame_timestamp: datetime
    ) -> None:
        """Record movement state for group"""
        for member in group_members:
            track_id = member.track_id

            if track_id not in self.movement_history:
                self.movement_history[track_id] = []

            self.movement_history[track_id].append(
                {"timestamp": frame_timestamp, "keypoints": member.keypoints}
            )

            # Keep recent history
            if len(self.movement_history[track_id]) > 300:
                self.movement_history[track_id].pop(0)

    def analyze_group_sync(
        self, group_members: List[DetectedPerson], group_id: Optional[str] = None
    ) -> Optional[GroupSyncMetrics]:
        """
        Analyze synchronization in group exercise

        Args:
            group_members: Members of group
            group_id: Optional group identifier

        Returns:
            Group synchronization metrics
        """
        if len(group_members) < 2:
            return None

        group_id = group_id or f"group_{datetime.utcnow().timestamp()}"
        member_ids = {m.track_id for m in group_members if m.track_id}

        try:
            # 1. Movement synchronization (joint angle similarity)
            movement_sync = self._compute_movement_sync(group_members)

            # 2. Gait phase alignment
            phase_alignment = self._compute_phase_alignment(group_members)

            # 3. Pace consistency
            pace_consistency = self._compute_pace_consistency(group_members)

            # 4. Formation stability
            formation_stability = self._compute_formation_stability(group_members)

            return GroupSyncMetrics(
                group_id=group_id,
                member_ids=member_ids,
                timestamp=datetime.utcnow(),
                movement_sync_score=movement_sync,
                phase_alignment=phase_alignment,
                pace_consistency=pace_consistency,
                formation_stability=formation_stability,
            )
        except Exception as e:
            logger.error(f"Group sync analysis error: {e}")
            return None

    def _compute_movement_sync(self, members: List[DetectedPerson]) -> float:
        """Compute movement synchronization score"""
        if len(members) < 2:
            return 0

        # Simplified: compute variance of keypoint positions
        all_x = []
        all_y = []

        for member in members:
            for kpt in member.keypoints.values():
                all_x.append(kpt.get("x", 0.5))
                all_y.append(kpt.get("y", 0.5))

        if len(all_x) == 0:
            return 0

        # Lower variance = higher sync
        x_var = np.var(all_x)
        y_var = np.var(all_y)
        avg_var = (x_var + y_var) / 2

        # Convert to 0-1 score (lower variance = higher score)
        sync_score = max(0, 1 - avg_var)
        return float(np.clip(sync_score, 0, 1))

    def _compute_phase_alignment(self, members: List[DetectedPerson]) -> float:
        """Compute % of members in same gait phase"""
        if len(members) < 2:
            return 0

        # Simplified: all members considered in phase if confidence > threshold
        in_phase = sum(1 for m in members if m.confidence > 0.7)

        return float(in_phase / len(members))

    def _compute_pace_consistency(self, members: List[DetectedPerson]) -> float:
        """Compute cadence consistency"""
        if len(members) < 2:
            return 0

        # Simplified: check if members have similar vertical oscillation
        # (In real system, would use actual cadence estimates)

        return 0.8  # Placeholder

    def _compute_formation_stability(self, members: List[DetectedPerson]) -> float:
        """Compute formation cohesion"""
        if len(members) < 2:
            return 0

        # Compute bounding box of all members
        x_positions = [m.bounding_box[0] for m in members]
        y_positions = [m.bounding_box[1] for m in members]

        x_spread = max(x_positions) - min(x_positions)
        y_spread = max(y_positions) - min(y_positions)

        total_spread = x_spread + y_spread

        # Lower spread = tighter formation
        stability = max(0, 1 - total_spread)

        return float(np.clip(stability, 0, 1))


if __name__ == "__main__":
    # Example usage
    tracker = MultiPersonTracker()

    # Simulate 3 people detected in frame
    persons = [
        DetectedPerson(person_id="p1", bounding_box=(0.1, 0.2, 0.3, 0.6), confidence=0.95),
        DetectedPerson(person_id="p2", bounding_box=(0.5, 0.2, 0.7, 0.6), confidence=0.92),
        DetectedPerson(person_id="p3", bounding_box=(0.75, 0.2, 0.95, 0.6), confidence=0.88),
    ]

    tracked = tracker.update(persons, datetime.utcnow())
    print(f"Tracked {len(tracked)} people")

    # Test group analysis
    analyzer = GroupExerciseAnalyzer()
    sync_metrics = analyzer.analyze_group_sync(list(tracked.values()), "group_001")
    print(f"Group sync: {sync_metrics.movement_sync_score:.2f}")
