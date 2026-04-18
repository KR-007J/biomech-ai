"""
Phase 2 API Integrations - Advanced Platform Features
======================================================

Integrates all Phase 2 modules into the main API:
- WebSocket real-time endpoints
- GraphQL API layer
- Async job queue integration
- Webhook event system
- Model versioning API
- Advanced analytics endpoints
- A/B testing API
- Fraud detection integration
"""

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging
import asyncio
import json

# Phase 2 modules
from async_job_queue import AsyncJobQueue, JobPriority
from realtime_websocket import RealtimeWebSocketHub, RealtimeEvents
from webhook_events import EventSystem, Event
from graphql_api import GraphQLServer
from model_versioning import ModelRegistry
from advanced_analytics import AdvancedAnalyticsEngine
from ab_testing import ABTestingEngine, AllocationStrategy
from fraud_detection import FraudDetectionEngine
from schemas import FeedbackRequest

logger = logging.getLogger(__name__)

# Initialize Phase 2 services
job_queue = AsyncJobQueue(max_queue_size=1000)
websocket_hub = RealtimeWebSocketHub(max_connections=10000)
event_system = EventSystem()
graphql_server = GraphQLServer()
model_registry = ModelRegistry()
analytics_engine = AdvancedAnalyticsEngine()
ab_engine = ABTestingEngine()
fraud_engine = FraudDetectionEngine()

# Create router
router = APIRouter(prefix="/api/v2", tags=["Phase 2 Advanced Features"])


# ==================== DATA MODELS ====================

class JobSubmissionRequest(BaseModel):
    """Async job submission request"""
    job_type: str = Field(..., description="Type of job (analysis, report, etc.)")
    payload: Dict[str, Any] = Field(..., description="Job-specific data")
    priority: str = Field("NORMAL", description="Job priority")
    user_id: Optional[str] = None
    dependencies: List[str] = Field(default_factory=list, description="Job dependencies")

class WebhookRegistrationRequest(BaseModel):
    """Webhook registration request"""
    url: str = Field(..., description="Webhook endpoint URL")
    secret: str = Field(..., description="HMAC secret for signature verification")
    events: List[str] = Field(..., description="Events to subscribe to")

class ModelRegistrationRequest(BaseModel):
    """Model registration request"""
    name: str
    version: str
    model_type: str
    metadata: Dict[str, Any] = Field(default_factory=dict)

class ExperimentCreationRequest(BaseModel):
    """A/B experiment creation request"""
    name: str
    variants: List[str]
    traffic_percentage: int = 100
    strategy: str = "RANDOM"

class CohortCreationRequest(BaseModel):
    """Analytics cohort creation request"""
    name: str
    criteria: Dict[str, Any]
    group_by: str = "month"


# ==================== TIER 10: ASYNC JOB QUEUE ENDPOINTS ====================

@router.post("/jobs/submit")
async def submit_async_job(request: JobSubmissionRequest, background_tasks: BackgroundTasks):
    """Submit job to async queue"""
    try:
        # Validate priority
        try:
            priority = JobPriority[request.priority.upper()]
        except KeyError:
            raise HTTPException(status_code=400, detail=f"Invalid priority: {request.priority}")

        # Submit job
        job_id = await job_queue.submit_job(
            job_type=request.job_type,
            payload=request.payload,
            priority=priority,
            user_id=request.user_id,
            dependencies=request.dependencies
        )

        # Start processing in background
        background_tasks.add_task(job_queue.process_job, job_id)

        return {
            "job_id": job_id,
            "status": "submitted",
            "message": "Job submitted to queue"
        }

    except Exception as e:
        logger.error(f"Job submission error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/jobs/{job_id}")
async def get_job_status(job_id: str):
    """Get job status and progress"""
    if job_id not in job_queue.jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    job = job_queue.jobs[job_id]
    return {
        "job_id": job_id,
        "status": job.status.value,
        "progress": job.progress,
        "priority": job.priority.value,
        "created_at": job.created_at.isoformat(),
        "started_at": job.started_at.isoformat() if job.started_at else None,
        "completed_at": job.completed_at.isoformat() if job.completed_at else None,
        "result": job.result,
        "error": job.error
    }

@router.get("/jobs/stats")
async def get_job_queue_stats():
    """Get job queue statistics"""
    return job_queue.get_stats()

@router.delete("/jobs/{job_id}")
async def cancel_job(job_id: str):
    """Cancel a queued or running job"""
    if job_id not in job_queue.jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    success = await job_queue.cancel_job(job_id)
    return {"cancelled": success}


# ==================== TIER 11: WEBSOCKET ENDPOINTS ====================

@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    """WebSocket endpoint for real-time updates"""
    await websocket.accept()

    try:
        # Add connection
        connection_id = f"ws-{user_id}-{id(websocket)}"
        await websocket_hub.add_connection(connection_id, user_id)

        logger.info(f"WebSocket connected: {connection_id} for user {user_id}")

        # Send welcome message
        await websocket.send_json({
            "type": "connection_established",
            "connection_id": connection_id,
            "channels": []
        })

        # Message handling loop
        while True:
            try:
                # Receive message with timeout
                data = await asyncio.wait_for(websocket.receive_json(), timeout=30.0)

                message_type = data.get("type")

                if message_type == "subscribe":
                    # Subscribe to channels
                    channels = data.get("channels", [])
                    for channel in channels:
                        await websocket_hub.subscribe(connection_id, channel)

                    await websocket.send_json({
                        "type": "subscribed",
                        "channels": channels
                    })

                elif message_type == "unsubscribe":
                    # Unsubscribe from channels
                    channels = data.get("channels", [])
                    for channel in channels:
                        await websocket_hub.unsubscribe(connection_id, channel)

                    await websocket.send_json({
                        "type": "unsubscribed",
                        "channels": channels
                    })

                elif message_type == "ping":
                    # Heartbeat response
                    await websocket.send_json({
                        "type": "pong",
                        "timestamp": datetime.utcnow().isoformat()
                    })

                else:
                    await websocket.send_json({
                        "type": "error",
                        "message": f"Unknown message type: {message_type}"
                    })

            except asyncio.TimeoutError:
                # Send ping to keep connection alive
                await websocket.send_json({"type": "ping"})
                continue

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {connection_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        # Cleanup connection
        await websocket_hub.remove_connection(connection_id)

@router.post("/ws/broadcast/{channel}")
async def broadcast_to_channel(channel: str, message: Dict[str, Any]):
    """Broadcast message to WebSocket channel"""
    try:
        await websocket_hub.broadcast_to_channel(channel, message)
        return {"status": "broadcasted", "channel": channel}
    except Exception as e:
        logger.error(f"Broadcast error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== TIER 12: WEBHOOK ENDPOINTS ====================

@router.post("/webhooks/register")
async def register_webhook(request: WebhookRegistrationRequest):
    """Register webhook endpoint"""
    try:
        webhook_id = await event_system.register_webhook(
            url=request.url,
            secret=request.secret,
            events=request.events
        )

        return {
            "webhook_id": webhook_id,
            "status": "registered",
            "events": request.events
        }

    except Exception as e:
        logger.error(f"Webhook registration error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/webhooks/{webhook_id}")
async def unregister_webhook(webhook_id: str):
    """Unregister webhook"""
    success = await event_system.unregister_webhook(webhook_id)
    if not success:
        raise HTTPException(status_code=404, detail="Webhook not found")

    return {"status": "unregistered"}

@router.get("/webhooks/{webhook_id}")
async def get_webhook_status(webhook_id: str):
    """Get webhook delivery status"""
    if webhook_id not in event_system.webhooks:
        raise HTTPException(status_code=404, detail="Webhook not found")

    webhook = event_system.webhooks[webhook_id]
    return {
        "webhook_id": webhook_id,
        "url": webhook.url,
        "events": webhook.events,
        "is_active": not webhook.circuit_breaker_open,
        "success_rate": webhook.success_count / max(webhook.success_count + webhook.failure_count, 1),
        "last_delivery": webhook.last_delivery.isoformat() if webhook.last_delivery else None
    }

@router.post("/events/publish")
async def publish_event(event_type: str, resource_id: str, data: Dict[str, Any] = None):
    """Publish custom event"""
    try:
        event = Event(
            event_type=event_type,
            resource_id=resource_id,
            data=data or {}
        )

        await event_system.publish_event(event)

        return {"status": "published", "event_type": event_type}

    except Exception as e:
        logger.error(f"Event publishing error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== TIER 13: GRAPHQL ENDPOINT ====================

@router.post("/graphql")
async def graphql_endpoint(query: str, variables: Dict[str, Any] = None, operation_name: str = None):
    """GraphQL query endpoint"""
    try:
        if not query:
            raise HTTPException(status_code=400, detail="Query is required")

        # Execute query
        result = graphql_server.execute_query(
            query=query,
            variables=variables or {},
            operation_name=operation_name
        )

        if result.get("errors"):
            return JSONResponse(
                status_code=400,
                content={"errors": result["errors"]}
            )

        return result

    except Exception as e:
        logger.error(f"GraphQL error: {e}")
        return JSONResponse(
            status_code=500,
            content={"errors": [{"message": str(e)}]}
        )

@router.get("/graphql/schema")
async def get_graphql_schema():
    """Get GraphQL schema introspection"""
    return {
        "schema": str(graphql_server.schema),
        "types": graphql_server.get_available_types()
    }


# ==================== TIER 14: MODEL VERSIONING ENDPOINTS ====================

@router.post("/models/register")
async def register_model(request: ModelRegistrationRequest):
    """Register new model version"""
    try:
        model_id = model_registry.register_model(
            name=request.name,
            version=request.version,
            model_type=request.model_type,
            metadata=request.metadata
        )

        return {
            "model_id": model_id,
            "status": "registered",
            "version": request.version
        }

    except Exception as e:
        logger.error(f"Model registration error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/models/{model_id}/approve")
async def approve_model(model_id: str, approver: str):
    """Approve model for deployment"""
    if model_id not in model_registry.models:
        raise HTTPException(status_code=404, detail="Model not found")

    model_registry.approve_model(model_id, approver)

    return {"status": "approved"}

@router.post("/models/{model_id}/deploy")
async def deploy_model(model_id: str, traffic_percentage: int = 100):
    """Deploy model to production"""
    if model_id not in model_registry.models:
        raise HTTPException(status_code=404, detail="Model not found")

    model_registry.deploy_model(model_id, traffic_percentage)

    return {"status": "deployed", "traffic_percentage": traffic_percentage}

@router.get("/models/{model_id}/compare")
async def compare_models(model_id: str, baseline_model_id: str):
    """Compare model performance"""
    if model_id not in model_registry.models or baseline_model_id not in model_registry.models:
        raise HTTPException(status_code=404, detail="Model not found")

    comparison = model_registry.compare_models(model_id, baseline_model_id)

    return comparison

@router.get("/models")
async def list_models():
    """List all registered models"""
    models = []
    for model_id, model in model_registry.models.items():
        models.append({
            "id": model_id,
            "name": model.name,
            "version": model.version,
            "status": model.status.value,
            "created_at": model.created_at.isoformat()
        })

    return {"models": models}


# ==================== TIER 15: ADVANCED ANALYTICS ENDPOINTS ====================

@router.post("/analytics/cohorts")
async def create_cohort(request: CohortCreationRequest):
    """Create analytics cohort"""
    try:
        cohort_id = analytics_engine.create_cohort(
            name=request.name,
            criteria=request.criteria,
            group_by=request.group_by
        )

        return {
            "cohort_id": cohort_id,
            "status": "created",
            "name": request.name
        }

    except Exception as e:
        logger.error(f"Cohort creation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analytics/cohorts/{cohort_id}/retention")
async def get_cohort_retention(cohort_id: str, users: List[Dict[str, Any]]):
    """Calculate cohort retention"""
    if cohort_id not in analytics_engine.cohorts:
        raise HTTPException(status_code=404, detail="Cohort not found")

    retention = analytics_engine.calculate_retention(cohort_id, users, days=[1, 7, 30, 90])

    return retention

@router.post("/analytics/funnel")
async def analyze_funnel(steps: List[str], user_journeys: List[Dict[str, Any]]):
    """Analyze conversion funnel"""
    try:
        funnel = analytics_engine.analyze_funnel(steps, user_journeys)
        return funnel

    except Exception as e:
        logger.error(f"Funnel analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analytics/segment")
async def create_segments(users: List[Dict[str, Any]], criteria: Dict[str, Any]):
    """Create user segments"""
    try:
        segments = analytics_engine.create_segments(users, criteria)
        return segments

    except Exception as e:
        logger.error(f"Segmentation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== TIER 16: A/B TESTING ENDPOINTS ====================

@router.post("/experiments")
async def create_experiment(request: ExperimentCreationRequest):
    """Create A/B experiment"""
    try:
        # Validate strategy
        try:
            strategy = AllocationStrategy[request.strategy.upper()]
        except KeyError:
            raise HTTPException(status_code=400, detail=f"Invalid strategy: {request.strategy}")

        experiment_id = ab_engine.create_experiment(
            name=request.name,
            variants=request.variants,
            traffic_percentage=request.traffic_percentage,
            strategy=strategy
        )

        return {
            "experiment_id": experiment_id,
            "status": "created",
            "variants": request.variants
        }

    except Exception as e:
        logger.error(f"Experiment creation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/experiments/{experiment_id}/start")
async def start_experiment(experiment_id: str):
    """Start A/B experiment"""
    if experiment_id not in ab_engine.experiments:
        raise HTTPException(status_code=404, detail="Experiment not found")

    ab_engine.start_experiment(experiment_id)

    return {"status": "started"}

@router.get("/experiments/{experiment_id}/allocate/{user_id}")
async def allocate_user_variant(experiment_id: str, user_id: str):
    """Allocate user to experiment variant"""
    if experiment_id not in ab_engine.experiments:
        raise HTTPException(status_code=404, detail="Experiment not found")

    variant = ab_engine.allocate_user(experiment_id, user_id)

    return {"variant": variant}

@router.post("/experiments/{experiment_id}/convert/{user_id}")
async def record_conversion(experiment_id: str, user_id: str, converted: bool = True):
    """Record conversion for user"""
    if experiment_id not in ab_engine.experiments:
        raise HTTPException(status_code=404, detail="Experiment not found")

    ab_engine.record_conversion(experiment_id, user_id, converted)

    return {"status": "recorded"}

@router.get("/experiments/{experiment_id}/results")
async def get_experiment_results(experiment_id: str):
    """Get experiment results"""
    if experiment_id not in ab_engine.experiments:
        raise HTTPException(status_code=404, detail="Experiment not found")

    results = ab_engine.analyze_results(experiment_id)

    return results


# ==================== TIER 17: FRAUD DETECTION ENDPOINTS ====================

@router.post("/fraud/check")
async def check_fraud_risk(user_id: str, actions: List[Dict[str, Any]]):
    """Check user for fraud risk"""
    try:
        risk_score = fraud_engine.calculate_risk_score(user_id, actions)

        return {
            "user_id": user_id,
            "risk_score": risk_score,
            "risk_level": fraud_engine.get_risk_level(risk_score).value
        }

    except Exception as e:
        logger.error(f"Fraud check error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/fraud/profile/{user_id}")
async def get_fraud_profile(user_id: str):
    """Get user fraud profile"""
    if user_id not in fraud_engine.user_profiles:
        raise HTTPException(status_code=404, detail="Profile not found")

    profile = fraud_engine.user_profiles[user_id]
    return {
        "user_id": user_id,
        "typical_login_hour": profile.typical_login_hour,
        "typical_location": profile.typical_location,
        "typical_device": profile.typical_device,
        "risk_factors": profile.risk_factors
    }

@router.post("/fraud/block/{user_id}")
async def block_user(user_id: str, reason: str = "Suspicious activity"):
    """Block user account"""
    blocked = fraud_engine.block_user(user_id, reason)

    return {"blocked": blocked, "reason": reason}

@router.get("/fraud/blocked")
async def get_blocked_users():
    """Get list of blocked users"""
    return {"blocked_users": list(fraud_engine.blocked_users)}


# ==================== INTEGRATION ENDPOINTS ====================

@router.post("/integrate/analysis-job")
async def integrate_analysis_with_job_queue(payload: FeedbackRequest, background_tasks: BackgroundTasks):
    """Integrate analysis with async job queue for long-running tasks"""
    try:
        # Submit analysis as async job
        job_id = await job_queue.submit_job(
            job_type="biomech_analysis",
            payload={
                "metrics": payload.metrics.dict(),
                "exercise_type": payload.exercise_type,
                "user_id": payload.user_id,
                "session_id": payload.session_id
            },
            priority=JobPriority.HIGH,
            user_id=payload.user_id
        )

        # Start processing
        background_tasks.add_task(job_queue.process_job, job_id)

        # Publish event
        await event_system.publish_event(Event(
            event_type="analysis.started",
            resource_id=payload.session_id or payload.user_id,
            data={"job_id": job_id}
        ))

        return {
            "job_id": job_id,
            "status": "processing",
            "message": "Analysis submitted to async queue"
        }

    except Exception as e:
        logger.error(f"Analysis job integration error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
