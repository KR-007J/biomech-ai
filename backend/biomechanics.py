import numpy as np

def calculate_angle(a, b, c):
    """
    Calculates the 2D angle (in degrees) at joint 'b' using the vector dot product.
    Formula: theta = arccos( (v1 dot v2) / (|v1| * |v2|) )
    Points a, b, c are [x, y].
    """
    a = np.array(a)
    b = np.array(b)
    c = np.array(c)

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

def get_biomechanical_analysis(keypoints):
    """
    Analyzes key joints and returns structured biomechanical data.
    """
    if not keypoints:
        return {}

    def get_pt(name):
        return [keypoints[name]['x'], keypoints[name]['y']]

    # Ideal ranges for common exercises (Example defaults)
    IDEAL_RANGES = {
        "knee": {"min": 85, "max": 100},
        "elbow": {"min": 45, "max": 160},
        "hip": {"min": 70, "max": 180}
    }

    results = {
        "angles": {},
        "ideal_ranges": IDEAL_RANGES,
        "deviations": {},
        "pose_confidence": 0.0
    }
    
    try:
        # Calculate Angles
        results["angles"]["left_elbow"] = calculate_angle(get_pt('LEFT_SHOULDER'), get_pt('LEFT_ELBOW'), get_pt('LEFT_WRIST'))
        results["angles"]["right_elbow"] = calculate_angle(get_pt('RIGHT_SHOULDER'), get_pt('RIGHT_ELBOW'), get_pt('RIGHT_WRIST'))
        results["angles"]["left_knee"] = calculate_angle(get_pt('LEFT_HIP'), get_pt('LEFT_KNEE'), get_pt('LEFT_ANKLE'))
        results["angles"]["right_knee"] = calculate_angle(get_pt('RIGHT_HIP'), get_pt('RIGHT_KNEE'), get_pt('RIGHT_ANKLE'))
        results["angles"]["left_hip"] = calculate_angle(get_pt('LEFT_SHOULDER'), get_pt('LEFT_HIP'), get_pt('LEFT_KNEE'))
        results["angles"]["right_hip"] = calculate_angle(get_pt('RIGHT_SHOULDER'), get_pt('RIGHT_HIP'), get_pt('RIGHT_KNEE'))

        # Calculate Deviations (Simplified)
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
        visibilities = [keypoints[name]['visibility'] for name in keypoints]
        results["pose_confidence"] = float(round(np.mean(visibilities), 3))
        
    except KeyError:
        pass
        
    return results
