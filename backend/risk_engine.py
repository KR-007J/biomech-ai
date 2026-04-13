def analyze_injury_risk(angles):
    """
    Evaluates injury risk based on joint angles.
    """
    risk_score = 0
    issues = []
    
    # Example Rules:
    
    # 1. Knee Hyperextension or deep strain
    if angles.get('left_knee_angle', 180) < 30 or angles.get('right_knee_angle', 180) < 30:
        risk_score += 40
        issues.append("Deep knee compression detected. Potential meniscus stress.")
    
    if angles.get('left_knee_angle', 180) > 175 or angles.get('right_knee_angle', 180) > 175:
        risk_score += 10 # Slight hyperextension risk
        
    # 2. Shoulder impingement (arm too high or weird angle during push/pull)
    if angles.get('left_shoulder_angle', 0) > 160 or angles.get('right_shoulder_angle', 0) > 160:
        risk_score += 20
        issues.append("Excessive shoulder elevation. Risk of impingement.")

    # 3. Back/Hip posture
    if angles.get('left_hip_angle', 180) < 70 or angles.get('right_hip_angle', 180) < 70:
        risk_score += 30
        issues.append("Acute hip angle. Check lower back rounding (lumbar flexion).")

    # Determine Level
    if risk_score >= 60:
        level = "HIGH"
    elif risk_score >= 30:
        level = "MEDIUM"
    else:
        level = "LOW"
        
    if not issues:
        issues.append("Form looks stable. Maintain control throughout the movement.")

    return {
        "risk_level": level,
        "risk_score": risk_score,
        "explanation": " | ".join(issues)
    }
