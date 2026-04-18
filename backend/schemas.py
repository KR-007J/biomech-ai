"""
Biomech AI - Pydantic Schemas and Data Models
=============================================

This module contains all input validation and response models for the 
Biomech AI platform, centralizing data definitions to avoid circular imports.
"""

from typing import Dict, Optional, Any, List
from pydantic import BaseModel, Field, field_validator
import logging

logger = logging.getLogger(__name__)

# ==================== CORE MODELS ====================

class MetricsData(BaseModel):
    """Biomechanical metrics from pose analysis"""
    angles: Dict[str, float] = Field(..., description="Joint angles in degrees")
    deviations: Dict[str, float] = Field(..., description="Deviations from ideal")
    pose_confidence: float = Field(..., ge=0, le=1)
    ideal_ranges: Optional[Dict[str, Dict[str, float]]] = None
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "angles": {"knee": 85.3, "hip": 92.1},
                "deviations": {"knee": 5.2, "hip": 2.1},
                "pose_confidence": 0.95
            }
        }
    }

class FeedbackRequest(BaseModel):
    """Exercise analysis request"""
    metrics: MetricsData
    exercise_type: str = Field(..., min_length=1, max_length=50)
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    
    @field_validator("exercise_type")
    @classmethod
    def validate_exercise(cls, v: str) -> str:
        VALID = ["squat", "pushup", "lunge", "deadlift", "bicep_curl",
                 "shoulder_press", "plank", "general", "jog", "sprint"]
        if v.lower() not in VALID:
            logger.warning(f"Unknown exercise: {v}")
        return v

class CoachFeedback(BaseModel):
    """AI-generated coaching feedback"""
    issue: str
    reason: str
    fix: str
    confidence: float = 0.95

class AnalysisResponse(BaseModel):
    """Complete analysis response"""
    status: str
    timestamp: float
    analysis_id: str
    summary: Dict[str, Any]
    coach_feedback: CoachFeedback
    performance_metrics: Dict[str, Any]

# ==================== USER & SESSION MODELS ====================

class ProfileData(BaseModel):
    """User profile"""
    id: str
    name: str
    email: str
    picture: Optional[str] = None
    stats: Optional[Dict[str, Any]] = None

class SessionData(BaseModel):
    """Workout session"""
    user_id: str
    exercise: str
    reps: int = Field(..., ge=0)
    score: float = Field(..., ge=0, le=100)
    duration: float = Field(..., ge=0)

# ==================== SYSTEM MODELS ====================

class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    timestamp: str
    version: str
    services: Dict[str, str]
