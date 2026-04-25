from typing import Any, Dict, List

import numpy as np


def calculate_angle(a: List[float], b: List[float], c: List[float]) -> float:
    """
    Calculates the angle at joint 'b' using the vector dot product.

    Formula: theta = arccos( (v1 dot v2) / (|v1| * |v2|) )

    Args:
        a: First point coordinates [x, y]
        b: Vertex point coordinates [x, y]
        c: Third point coordinates [x, y]

    Returns:
        Angle in degrees (0-180)

    Raises:
        ValueError: If points are invalid or cause numerical errors
    """
    try:
        a = np.array(a, dtype=np.float32)
        b = np.array(b, dtype=np.float32)
        c = np.array(c, dtype=np.float32)

        # Create vectors from the vertex b
        v1 = a - b
        v2 = c - b

        # Dot product and magnitudes
        dot_product = np.dot(v1, v2)
        norm_v1 = np.linalg.norm(v1)
        norm_v2 = np.linalg.norm(v2)

        # Cosine of the angle
        cos_theta = dot_product / (norm_v1 * norm_v2 + 1e-6)
        cos_theta = np.clip(cos_theta, -1.0, 1.0)

        angle = np.degrees(np.arccos(cos_theta))
        return float(round(angle, 2))
    except Exception as e:
        raise ValueError(f"Failed to calculate angle: {e}")


def get_biomechanical_analysis(
    keypoints: Dict[str, Dict[str, float]],
) -> Dict[str, Any]:
    """
    Analyzes key joints and returns structured biomechanical data.

    Args:
        keypoints: Dict of landmark positions with visibility scores

    Returns:
        Dict containing angles, deviations, and pose confidence
    """
    if not keypoints:
        return {}

    def get_pt(name: str) -> List[float]:
        """Extract x, y coordinates from keypoint"""
        return [keypoints[name]["x"], keypoints[name]["y"]]

    # Ideal ranges for common exercises (Example defaults)
    IDEAL_RANGES: Dict[str, Dict[str, float]] = {
        "knee": {"min": 85, "max": 100},
        "elbow": {"min": 45, "max": 160},
        "hip": {"min": 70, "max": 180},
    }

    results: Dict[str, Any] = {
        "angles": {},
        "ideal_ranges": IDEAL_RANGES,
        "deviations": {},
        "pose_confidence": 0.0,
    }

    try:
        # Calculate Angles
        results["angles"]["left_elbow"] = calculate_angle(get_pt("LEFT_SHOULDER"), get_pt("LEFT_ELBOW"), get_pt("LEFT_WRIST"))
        results["angles"]["right_elbow"] = calculate_angle(get_pt("RIGHT_SHOULDER"), get_pt("RIGHT_ELBOW"), get_pt("RIGHT_WRIST"))
        results["angles"]["left_knee"] = calculate_angle(get_pt("LEFT_HIP"), get_pt("LEFT_KNEE"), get_pt("LEFT_ANKLE"))
        results["angles"]["right_knee"] = calculate_angle(get_pt("RIGHT_HIP"), get_pt("RIGHT_KNEE"), get_pt("RIGHT_ANKLE"))
        results["angles"]["left_hip"] = calculate_angle(get_pt("LEFT_SHOULDER"), get_pt("LEFT_HIP"), get_pt("LEFT_KNEE"))
        results["angles"]["right_hip"] = calculate_angle(get_pt("RIGHT_SHOULDER"), get_pt("RIGHT_HIP"), get_pt("RIGHT_KNEE"))

        # Calculate Deviations
        for joint, value in results["angles"].items():
            base_joint = "knee" if "knee" in joint else ("elbow" if "elbow" in joint else "hip")
            ideal = IDEAL_RANGES[base_joint]
            if value < ideal["min"]:
                results["deviations"][joint] = float(round(value - ideal["min"], 2))
            elif value > ideal["max"]:
                results["deviations"][joint] = float(round(value - ideal["max"], 2))
            else:
                results["deviations"][joint] = 0.0

        # Overall Confidence
        visibilities = [keypoints[name]["visibility"] for name in keypoints]
        results["pose_confidence"] = float(round(np.mean(visibilities), 3))

    except KeyError:
        pass

    return results
