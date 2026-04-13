import numpy as np

def calculate_angle(a, b, c):
    """
    Calculates the angle at point b given three points a, b, and c.
    Points are expected to be [x, y] or [x, y, z].
    """
    a = np.array(a) # First
    b = np.array(b) # Mid
    c = np.array(c) # End
    
    radians = np.arctan2(c[1]-b[1], c[0]-b[0]) - np.arctan2(a[1]-b[1], a[0]-b[0])
    angle = np.abs(radians*180.0/np.pi)
    
    if angle > 180.0:
        angle = 360-angle
        
    return angle

def get_biomechanical_analysis(keypoints):
    """
    Analyzes key joints and returns angles.
    """
    if not keypoints:
        return {}

    # Define common joint indices or names
    # Keypoints are structured as { 'LEFT_SHOULDER': {x, y, z}, ... }
    
    def get_pt(name):
        return [keypoints[name]['x'], keypoints[name]['y']]

    analysis = {}
    
    try:
        # Elbow Angles
        analysis['left_elbow_angle'] = calculate_angle(
            get_pt('LEFT_SHOULDER'), get_pt('LEFT_ELBOW'), get_pt('LEFT_WRIST')
        )
        analysis['right_elbow_angle'] = calculate_angle(
            get_pt('RIGHT_SHOULDER'), get_pt('RIGHT_ELBOW'), get_pt('RIGHT_WRIST')
        )
        
        # Knee Angles
        analysis['left_knee_angle'] = calculate_angle(
            get_pt('LEFT_HIP'), get_pt('LEFT_KNEE'), get_pt('LEFT_ANKLE')
        )
        analysis['right_knee_angle'] = calculate_angle(
            get_pt('RIGHT_HIP'), get_pt('RIGHT_KNEE'), get_pt('RIGHT_ANKLE')
        )
        
        # Hip Angles
        analysis['left_hip_angle'] = calculate_angle(
            get_pt('LEFT_SHOULDER'), get_pt('LEFT_HIP'), get_pt('LEFT_KNEE')
        )
        analysis['right_hip_angle'] = calculate_angle(
            get_pt('RIGHT_SHOULDER'), get_pt('RIGHT_HIP'), get_pt('RIGHT_KNEE')
        )
        
        # Shoulder Angles
        analysis['left_shoulder_angle'] = calculate_angle(
            get_pt('LEFT_ELBOW'), get_pt('LEFT_SHOULDER'), get_pt('LEFT_HIP')
        )
        analysis['right_shoulder_angle'] = calculate_angle(
            get_pt('RIGHT_ELBOW'), get_pt('RIGHT_SHOULDER'), get_pt('RIGHT_HIP')
        )
        
    except KeyError:
        # Some keypoints might be missing
        pass
        
    return analysis
