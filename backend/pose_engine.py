import cv2
import mediapipe as mp
import numpy as np

class PoseEngine:
    def __init__(self):
        self.mp_pose = mp.solutions.pose
        self.pose = self.mp_pose.Pose(static_image_mode=False, min_detection_confidence=0.5, min_tracking_confidence=0.5)
        self.mp_drawing = mp.solutions.drawing_utils

    def process_frame(self, frame):
        # Convert the BGR image to RGB
        image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.pose.process(image_rgb)
        
        if not results.pose_landmarks:
            return None, frame

        landmarks = results.pose_landmarks.landmark
        
        # Extract keypoints
        keypoints = {}
        for idx, landmark in enumerate(landmarks):
            keypoints[self.mp_pose.PoseLandmark(idx).name] = {
                "x": landmark.x,
                "y": landmark.y,
                "z": landmark.z,
                "visibility": landmark.visibility
            }

        return keypoints, results.pose_landmarks

    def draw_landmarks(self, frame, landmarks):
        annotated_image = frame.copy()
        self.mp_drawing.draw_landmarks(
            annotated_image, 
            landmarks, 
            self.mp_pose.POSE_CONNECTIONS
        )
        return annotated_image
