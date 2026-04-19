import logging
from typing import Any, Dict, Optional, Tuple

import cv2
import numpy as np

logger = logging.getLogger(__name__)

# Try to import mediapipe, but don't fail if unavailable
try:
    import mediapipe as mp

    HAS_MEDIAPIPE = True
except ImportError:
    HAS_MEDIAPIPE = False
    logger.warning("MediaPipe not available - pose detection disabled")


class PoseEngine:
    """MediaPipe-based pose detection engine for biomechanical analysis"""

    def __init__(self) -> None:
        """Initialize pose estimation model"""
        if not HAS_MEDIAPIPE:
            logger.warning("PoseEngine initialized without MediaPipe")
            self.pose = None
            self.mp_drawing = None
            return

        try:
            # Try new MediaPipe tasks API first
            from mediapipe.tasks import python
            from mediapipe.tasks.python import vision

            self.pose = None  # Using new API
            logger.info("Using MediaPipe Tasks API")
        except ImportError:
            try:
                # Fall back to legacy solutions API
                self.mp_pose = mp.solutions.pose
                self.pose = self.mp_pose.Pose(
                    static_image_mode=False,
                    min_detection_confidence=0.5,
                    min_tracking_confidence=0.5,
                )
                self.mp_drawing = mp.solutions.drawing_utils
                logger.info("Using MediaPipe solutions API")
            except Exception as e:
                logger.error(f"Failed to initialize pose model: {e}")
                self.pose = None
                self.mp_drawing = None

    def process_frame(
        self, frame: np.ndarray
    ) -> Tuple[Optional[Dict[str, Dict[str, float]]], Optional[Any]]:
        """
        Process a single frame and extract pose landmarks.

        Args:
            frame: Input frame in BGR format (numpy array)

        Returns:
            Tuple of (keypoints dict, pose_landmarks object) or (None, frame) if detection fails
        """
        if self.pose is None:
            logger.warning("Pose engine not available - returning None")
            return None, frame

        try:
            # Convert the BGR image to RGB
            image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self.pose.process(image_rgb)

            if not results.pose_landmarks:
                return None, frame

            landmarks = results.pose_landmarks.landmark

            # Extract keypoints
            keypoints: Dict[str, Dict[str, float]] = {}
            for idx, landmark in enumerate(landmarks):
                landmark_name = self.mp_pose.PoseLandmark(idx).name
                keypoints[landmark_name] = {
                    "x": landmark.x,
                    "y": landmark.y,
                    "z": landmark.z,
                    "visibility": landmark.visibility,
                }

            return keypoints, results.pose_landmarks
        except Exception as e:
            logger.error(f"Error in process_frame: {e}")
            return None, frame

    def draw_landmarks(self, frame: np.ndarray, landmarks: Any) -> np.ndarray:
        """
        Draw pose landmarks on the frame.

        Args:
            frame: Input frame to draw on
            landmarks: MediaPipe pose landmarks

        Returns:
            Annotated frame with drawn landmarks
        """
        if self.mp_drawing is None or landmarks is None:
            return frame.copy()

        try:
            annotated_image = frame.copy()
            self.mp_drawing.draw_landmarks(
                annotated_image, landmarks, self.mp_pose.POSE_CONNECTIONS
            )
            return annotated_image
        except Exception as e:
            logger.error(f"Error drawing landmarks: {e}")
            return frame.copy()
