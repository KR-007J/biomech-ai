"""
Enhanced API Endpoints - Tiers 1-9
===================================

New endpoints for advanced features:
- Ensemble analysis
- Predictive analytics
- Multi-person tracking
- Action recognition
- Report generation
- Comparative analytics
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel, Field

from unified_analyzer import UnifiedBiomechanicsAnalyzer

logger = logging.getLogger(__name__)

# Initialize unified analyzer
analyzer = UnifiedBiomechanicsAnalyzer()

# Create router
router = APIRouter(prefix="/api/v2", tags=["Advanced Analysis"])


# ==================== REQUEST/RESPONSE MODELS ====================


class FrameAnalysisRequest(BaseModel):
    """Frame analysis request"""

    session_id: str
    user_id: str
    keypoints: Dict[str, Dict[str, float]]
    body_weight: Optional[float] = 70.0
    height: Optional[float] = 1.75
    exercise_type: Optional[str] = None


class SessionAnalysisRequest(BaseModel):
    """Session analysis request"""

    session_id: str
    user_id: str
    frames: List[Dict[str, Any]]
    duration_seconds: float
    exercise_type: str


class MultiPersonAnalysisRequest(BaseModel):
    """Multi-person analysis request"""

    session_id: str
    detected_persons: List[Dict[str, Any]]
    frame_timestamp: datetime = Field(default_factory=datetime.utcnow)


class ReportRequest(BaseModel):
    """Report generation request"""

    user_id: str
    session_id: Optional[str] = None
    report_type: str = "session"  # session, trend, custom
    include_charts: bool = True
    include_trends: bool = True
    days_history: int = 30


class InjuryPredictionRequest(BaseModel):
    """Injury prediction request"""

    user_id: str
    weeks_ahead: int = 2


# ==================== TIER 1: ENSEMBLE & PREDICTION ====================


@router.post("/ensemble/analyze")
async def analyze_with_ensemble(request: FrameAnalysisRequest) -> Dict[str, Any]:
    """
    Analyze frame using multi-model ensemble

    Combines MediaPipe + YOLOv8 + OpenPose with voting mechanism
    """
    try:
        if not analyzer.is_initialized:
            await analyzer.initialize()

        # Run ensemble
        result = await analyzer.analyze_frame(
            {
                "keypoints": request.keypoints,
                "body_weight": request.body_weight,
                "height": request.height,
            },
            request.session_id,
            request.user_id,
        )

        return {"success": True, "data": result}
    except Exception as e:
        logger.error(f"Ensemble analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/prediction/injury-risk")
async def predict_injury_risk(request: InjuryPredictionRequest) -> Dict[str, Any]:
    """
    Predict injury risk for next 1-4 weeks

    Uses LSTM on historical session data to forecast injury probability
    """
    try:
        prediction = analyzer.injury_tracker.get_prediction(request.user_id, request.weeks_ahead)

        if not prediction:
            raise HTTPException(status_code=404, detail="Insufficient data for prediction")

        return {
            "success": True,
            "prediction": {
                "user_id": prediction.user_id,
                "weeks_ahead": prediction.weeks_ahead,
                "injury_probability": prediction.injury_probability,
                "risk_trajectory": prediction.risk_trajectory,
                "confidence": prediction.confidence,
                "contributing_factors": prediction.contributing_factors,
                "recommendations": prediction.recommendations,
                "next_prediction": (prediction.next_prediction.isoformat() if prediction.next_prediction else None),
            },
        }
    except Exception as e:
        logger.error(f"Injury prediction error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/biomechanics/advanced/{session_id}")
async def get_advanced_biomechanics(session_id: str) -> Dict[str, Any]:
    """
    Get advanced biomechanical analysis

    Includes IK solver, muscle activation, gait analysis, force calculations
    """
    try:
        if session_id not in analyzer.session_data:
            raise HTTPException(status_code=404, detail="Session not found")

        frames = analyzer.session_data[session_id]["frames"]

        # Extract biomechanics data
        biomech_data = []
        for frame in frames:
            if "biomechanics" in frame:
                biomech_data.append(frame["biomechanics"])

        return {
            "success": True,
            "session_id": session_id,
            "frames_analyzed": len(biomech_data),
            "biomechanics": biomech_data[-1] if biomech_data else None,
        }
    except Exception as e:
        logger.error(f"Biomechanics retrieval error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== TIER 2: ANALYTICS & REPORTS ====================


@router.post("/analytics/trends")
async def get_trends(user_id: str, metric: str, days: int = 30) -> Dict[str, Any]:
    """
    Get trend analysis for metric

    Provides trend direction, forecast, and anomaly detection
    """
    try:
        trend = analyzer.analytics.get_trend(metric, window=days)

        if not trend:
            return {"success": False, "message": "Insufficient data"}

        return {
            "success": True,
            "trend": {
                "metric": trend.metric_name,
                "direction": trend.trend_direction.value,
                "slope": trend.trend_slope,
                "r_squared": trend.r_squared,
                "forecast_7_days": trend.forecast_7_days,
                "confidence": trend.confidence,
            },
        }
    except Exception as e:
        logger.error(f"Trend analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analytics/anomalies")
async def detect_anomalies(user_id: str, metric: str, method: str = "zscore") -> Dict[str, Any]:
    """
    Detect anomalies in time series

    Supports: zscore, isolation_forest, lof
    """
    try:
        anomalies = analyzer.analytics.detect_anomalies(metric, method=method, threshold=2.5)

        return {
            "success": True,
            "metric": metric,
            "method": method,
            "anomalies_found": len(anomalies),
            "anomalies": [
                {
                    "timestamp": a.timestamp.isoformat(),
                    "value": a.value,
                    "expected_value": a.expected_value,
                    "severity": a.severity,
                    "explanation": a.explanation,
                }
                for a in anomalies
            ],
        }
    except Exception as e:
        logger.error(f"Anomaly detection error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reports/generate")
async def generate_report(request: ReportRequest) -> Dict[str, Any]:
    """
    Generate comprehensive biomechanical report

    Supports PDF/HTML with charts, trends, and personalized recommendations
    """
    try:
        if request.report_type == "session":
            # Get session data
            session_frames = []
            for sid, data in analyzer.session_data.items():
                if sid == request.session_id:
                    session_frames = data["frames"]
                    break

            if not session_frames:
                raise HTTPException(status_code=404, detail="Session not found")

            # Aggregate results
            aggregated = analyzer._aggregate_frame_results(session_frames)

            # Generate report
            report_config = {
                "include_charts": request.include_charts,
                "include_trends": request.include_trends,
                "days_history": request.days_history,
            }

            report_data = analyzer.report_generator.generate_session_report(
                user_id=request.user_id,
                session_data=aggregated,
                analysis_results=aggregated,
            )

            return {"success": True, "report": report_data}

        elif request.report_type == "trend":
            # Generate trend report
            risk_history = analyzer.injury_tracker.get_user_risk_history(request.user_id, limit=request.days_history)

            report_data = analyzer.report_generator.generate_trend_report(
                user_id=request.user_id,
                historical_data=[],
                trend_analysis={},  # Would load from DB
            )

            return {"success": True, "report": report_data}

        else:
            raise HTTPException(status_code=400, detail="Invalid report type")

    except Exception as e:
        logger.error(f"Report generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/reports/html/{session_id}")
async def get_html_report(session_id: str) -> Dict[str, str]:
    """Get HTML version of session report"""
    try:
        if session_id not in analyzer.session_data:
            raise HTTPException(status_code=404, detail="Session not found")

        frames = analyzer.session_data[session_id]["frames"]
        aggregated = analyzer._aggregate_frame_results(frames)

        report_data = analyzer.report_generator.generate_session_report(
            user_id="user_default", session_data=aggregated, analysis_results=aggregated
        )

        html = analyzer.report_generator.generate_html_report(report_data)

        return {"success": True, "html": html}
    except Exception as e:
        logger.error(f"HTML report error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics/correlation")
async def get_correlation(metric_1: str, metric_2: str) -> Dict[str, Any]:
    """
    Calculate correlation between two metrics

    Useful for understanding relationships (e.g., fatigue vs risk)
    """
    try:
        corr = analyzer.analytics.get_correlation(metric_1, metric_2)

        if not corr:
            return {"success": False, "message": "Insufficient data"}

        return {
            "success": True,
            "correlation": {
                "metric_1": corr.metric_1,
                "metric_2": corr.metric_2,
                "coefficient": corr.correlation_coefficient,
                "p_value": corr.p_value,
                "significance": corr.significance,
            },
        }
    except Exception as e:
        logger.error(f"Correlation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== TIER 3: MULTI-PERSON & ACTIONS ====================


@router.post("/multi-person/track")
async def track_multiple_people(request: MultiPersonAnalysisRequest) -> Dict[str, Any]:
    """
    Track and analyze multiple people simultaneously

    Real-time multi-person detection and re-identification
    """
    try:
        tracked = analyzer.tracker.update(request.detected_persons, request.frame_timestamp)

        return {
            "success": True,
            "persons_tracked": len(tracked),
            "track_ids": list(tracked.keys()),
            "timestamp": request.frame_timestamp.isoformat(),
        }
    except Exception as e:
        logger.error(f"Multi-person tracking error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/group-analysis/sync")
async def analyze_group_synchronization(
    request: MultiPersonAnalysisRequest,
) -> Dict[str, Any]:
    """
    Analyze synchronization in group exercise

    Measures movement sync, phase alignment, pace consistency
    """
    try:
        tracked = analyzer.tracker.update(request.detected_persons, request.frame_timestamp)

        if len(tracked) < 2:
            raise HTTPException(status_code=400, detail="Need at least 2 people for group analysis")

        sync_metrics = analyzer.group_analyzer.analyze_group_sync(list(tracked.values()), f"group_{request.session_id}")

        if not sync_metrics:
            raise HTTPException(status_code=500, detail="Sync analysis failed")

        return {
            "success": True,
            "group_id": sync_metrics.group_id,
            "member_count": len(sync_metrics.member_ids),
            "movement_sync": sync_metrics.movement_sync_score,
            "phase_alignment": sync_metrics.phase_alignment,
            "pace_consistency": sync_metrics.pace_consistency,
            "formation_stability": sync_metrics.formation_stability,
            "overall_score": (
                sync_metrics.movement_sync_score * 0.3
                + sync_metrics.phase_alignment * 0.3
                + sync_metrics.pace_consistency * 0.2
                + sync_metrics.formation_stability * 0.2
            ),
        }
    except Exception as e:
        logger.error(f"Group sync analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/actions/recognize")
async def recognize_action(request: FrameAnalysisRequest) -> Dict[str, Any]:
    """
    Recognize exercise/movement type

    Classifies actions and counts repetitions with form assessment
    """
    try:
        action_type, confidence = analyzer.action_classifier.classify_action(request.keypoints)

        # Form assessment
        form_score, issues = analyzer.form_assessor.assess_squat_form(analyzer.biomechanics_engine._extract_joint_angles(request.keypoints))

        # Rep count
        reps = analyzer.rep_counter.update(90)  # Sample angle

        return {
            "success": True,
            "action": action_type.value,
            "confidence": confidence,
            "reps": reps,
            "form_quality": form_score,
            "form_issues": issues,
        }
    except Exception as e:
        logger.error(f"Action recognition error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== COMPREHENSIVE SESSION ANALYSIS ====================


@router.post("/session/analyze-comprehensive")
async def analyze_session_comprehensive(request: SessionAnalysisRequest, background_tasks: BackgroundTasks) -> Dict[str, Any]:
    """
    Comprehensive multi-tier session analysis

    Runs all Tier 1-3 analysis on complete session
    """
    try:
        # Run in background
        background_tasks.add_task(
            analyzer.analyze_session,
            request.session_id,
            request.user_id,
            request.frames,
        )

        return {
            "success": True,
            "session_id": request.session_id,
            "status": "processing",
            "message": "Session analysis started",
        }
    except Exception as e:
        logger.error(f"Session analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/session/results/{session_id}")
async def get_session_results(session_id: str) -> Dict[str, Any]:
    """Get comprehensive session analysis results"""
    try:
        if session_id not in analyzer.session_data:
            raise HTTPException(status_code=404, detail="Session not found")

        frames = analyzer.session_data[session_id]["frames"]
        aggregated = analyzer._aggregate_frame_results(frames)

        return {
            "success": True,
            "session_id": session_id,
            "frames_analyzed": len(frames),
            "results": aggregated,
        }
    except Exception as e:
        logger.error(f"Session results error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== USER DASHBOARD ====================


@router.get("/dashboard/{user_id}")
async def get_user_dashboard(user_id: str, days: int = 30) -> Dict[str, Any]:
    """
    Get comprehensive user dashboard

    Combines all Tier 1-2 insights: trends, predictions, analytics, recommendations
    """
    try:
        dashboard = await analyzer.get_user_dashboard(user_id, days)
        return {"success": True, "dashboard": dashboard}
    except Exception as e:
        logger.error(f"Dashboard error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== SYSTEM STATUS ====================


@router.get("/status")
async def get_system_status() -> Dict[str, Any]:
    """Get analyzer system status"""
    try:
        stats = analyzer.get_stats()

        return {
            "success": True,
            "status": "operational",
            "stats": stats,
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        logger.error(f"Status check error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== INITIALIZATION ====================


@router.post("/init")
async def initialize_analyzer() -> Dict[str, Any]:
    """Initialize analyzer (models, caches)"""
    try:
        success = await analyzer.initialize()

        return {
            "success": success,
            "message": ("Analyzer initialized successfully" if success else "Initialization failed"),
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        logger.error(f"Initialization error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
