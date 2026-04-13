def analyze_injury_risk(analysis_data):
    """
    Evaluates injury risk based on biomechanical deviations and confidence levels.
    """
    angles = analysis_data.get('angles', {})
    deviations = analysis_data.get('deviations', {})
    pose_confidence = analysis_data.get('pose_confidence', 1.0)
    
    risk_score = 0
    issues = []
    
    # Weight settings
    WEIGHTS = {
        "knee": 1.5,
        "hip": 1.2,
        "elbow": 0.8
    }
    
    for joint, deviation in deviations.items():
        if abs(deviation) > 0:
            base_joint = "knee" if "knee" in joint else ("elbow" if "elbow" in joint else "hip")
            penalty = abs(deviation) * WEIGHTS.get(base_joint, 1.0)
            risk_score += penalty
            
            if abs(deviation) > 20:
                issues.append(f"Critical {joint.replace('_', ' ')} deviation: {deviation}°")
            elif abs(deviation) > 10:
                issues.append(f"Notable {joint.replace('_', ' ')} strain: {deviation}°")

    # Final scaling
    risk_score = min(100, risk_score)
    
    # Confidence penalty
    if pose_confidence < 0.7:
        risk_score = min(100, risk_score + 15)
        issues.append("Low detection confidence. Analysis may be inaccurate.")

    # Determine Level
    if risk_score >= 60:
        level = "HIGH"
    elif risk_score >= 30:
        level = "MEDIUM"
    else:
        level = "LOW"
        
    if not issues:
        issues.append("Optimal alignment detected.")

    return {
        "risk_level": level,
        "risk_score": float(round(risk_score, 2)),
        "risk_reason": " | ".join(issues),
        "pose_confidence": pose_confidence
    }
