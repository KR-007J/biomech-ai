from typing import Any, Dict, List


def analyze_injury_risk(analysis_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Evaluates injury risk based on biomechanical deviations and confidence levels.

    Args:
        analysis_data: Dict containing angles, deviations, and pose_confidence

    Returns:
        Dict with risk_level, risk_score, risk_reason, and pose_confidence

    Risk Levels:
        - LOW: risk_score < 30
        - MEDIUM: 30 <= risk_score < 60
        - HIGH: risk_score >= 60
    """
    angles: Dict[str, float] = analysis_data.get("angles", {})
    deviations: Dict[str, float] = analysis_data.get("deviations", {})
    pose_confidence: float = analysis_data.get("pose_confidence", 1.0)

    risk_score: float = 0
    issues: List[str] = []

    # Weight settings for different joints
    WEIGHTS: Dict[str, float] = {
        "knee": 1.5,  # Highest - most prone to injury
        "hip": 1.2,  # Moderate - important stability point
        "elbow": 0.8,  # Lower - less critical
    }

    # Calculate risk from deviations
    for joint, deviation in deviations.items():
        if abs(deviation) > 0:
            base_joint = "knee" if "knee" in joint else ("elbow" if "elbow" in joint else "hip")
            penalty = abs(deviation) * WEIGHTS.get(base_joint, 1.0)
            risk_score += penalty

            if abs(deviation) > 20:
                issues.append(f"Critical {joint.replace('_', ' ')} deviation: {deviation}°")
            elif abs(deviation) > 10:
                issues.append(f"Notable {joint.replace('_', ' ')} strain: {deviation}°")

    # Final scaling (cap at 100)
    risk_score = min(100.0, risk_score)

    # Confidence penalty - lower confidence increases risk
    if pose_confidence < 0.7:
        risk_score = min(100.0, risk_score + 15)
        issues.append("Low detection confidence. Analysis may be inaccurate.")

    # Determine Risk Level
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
        "pose_confidence": pose_confidence,
    }
