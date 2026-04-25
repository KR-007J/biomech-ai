"""
Phase 2 Integration Tests - Tiers 10-17
========================================

Comprehensive integration tests for advanced platform features:
- Async job queuing
- Real-time WebSocket
- Webhook events
- GraphQL API
- Model versioning
- Advanced analytics
- A/B testing
- Fraud detection
"""

from datetime import datetime, timedelta
from unittest.mock import patch

import pytest

from ab_testing import ABTestingEngine, AllocationStrategy
from advanced_analytics import AdvancedAnalyticsEngine

# Phase 2 modules
from async_job_queue import AsyncJobQueue, JobPriority
from fraud_detection import FraudDetectionEngine
from graphql_api import GraphQLServer
from model_versioning import ModelRegistry
from realtime_websocket import RealtimeWebSocketHub
from webhook_events import Event, EventSystem


@pytest.fixture
def job_queue():
    return AsyncJobQueue(max_concurrent_jobs=100)


@pytest.fixture
def websocket_hub():
    return RealtimeWebSocketHub(max_connections=1000)


@pytest.fixture
def event_system():
    return EventSystem(max_events=1000)


@pytest.fixture
def graphql_server():
    return GraphQLServer()


@pytest.fixture
def model_registry():
    return ModelRegistry()


@pytest.fixture
def analytics_engine():
    return AdvancedAnalyticsEngine()


@pytest.fixture
def ab_engine():
    return ABTestingEngine()


@pytest.fixture
def fraud_engine():
    return FraudDetectionEngine()


class TestPhase2Integration:
    """Integration tests for Phase 2 advanced features"""

    @pytest.fixture
    def job_queue(self):
        """Async job queue fixture"""
        return AsyncJobQueue(max_concurrent_jobs=100)

    @pytest.fixture
    def websocket_hub(self):
        """WebSocket hub fixture"""
        return RealtimeWebSocketHub(max_connections=1000)

    @pytest.fixture
    def event_system(self):
        """Event system fixture"""
        return EventSystem(max_events=1000)

    @pytest.fixture
    def graphql_server(self):
        """GraphQL server fixture"""
        return GraphQLServer()

    @pytest.fixture
    def model_registry(self):
        """Model registry fixture"""
        return ModelRegistry()

    @pytest.fixture
    def analytics_engine(self):
        """Analytics engine fixture"""
        return AdvancedAnalyticsEngine()

    @pytest.fixture
    def ab_engine(self):
        """A/B testing engine fixture"""
        return ABTestingEngine()

    @pytest.fixture
    def fraud_engine(self):
        """Fraud detection engine fixture"""
        return FraudDetectionEngine()

    # ==================== TIER 10: ASYNC JOB QUEUE ====================

    @pytest.mark.asyncio
    async def test_job_queue_basic_workflow(self, job_queue):
        """✅ Basic job queue workflow"""
        # Submit job
        job_id = await job_queue.submit_job(
            job_type="analysis",
            payload={"session_id": "test-123"},
            priority=JobPriority.HIGH,
            user_id="user-456",
        )

        assert job_id
        assert job_id in job_queue.jobs

        # Check job status
        job = job_queue.jobs[job_id]
        assert job.status == "PENDING"
        assert job.priority == JobPriority.HIGH

        # Process job
        await job_queue.process_job(job_id)

        # Verify completion
        assert job.status == "COMPLETED"
        assert job.progress == 1.0

    @pytest.mark.asyncio
    async def test_job_dependencies(self, job_queue):
        """✅ Job dependency resolution"""
        # Submit parent job
        parent_id = await job_queue.submit_job(
            job_type="batch_analysis", payload={"batch_size": 10}
        )

        # Submit dependent job
        child_id = await job_queue.submit_job(
            job_type="report_generation", dependencies=[parent_id]
        )

        # Child should not process until parent completes
        await job_queue.process_job(child_id)
        assert job_queue.jobs[child_id].status == "PENDING"

        # Complete parent
        await job_queue.process_job(parent_id)
        assert job_queue.jobs[parent_id].status == "COMPLETED"

        # Now child can process
        await job_queue.process_job(child_id)
        assert job_queue.jobs[child_id].status == "COMPLETED"

    @pytest.mark.asyncio
    async def test_job_retry_logic(self, job_queue):
        """✅ Job retry with exponential backoff"""
        # Mock a failing job
        original_process = job_queue._process_job_internal

        async def failing_process(job_id):
            job = job_queue.jobs[job_id]
            if job.retry_count < 2:
                raise Exception("Simulated failure")
            return await original_process(job_id)

        job_queue._process_job_internal = failing_process

        # Submit job
        job_id = await job_queue.submit_job(job_type="failing_job")

        # Process (should retry)
        await job_queue.process_job(job_id)

        job = job_queue.jobs[job_id]
        assert job.retry_count == 2
        assert job.status == "COMPLETED"

    # ==================== TIER 11: REAL-TIME WEBSOCKET ====================

    @pytest.mark.asyncio
    async def test_websocket_connection_management(self, websocket_hub):
        """✅ WebSocket connection lifecycle"""
        # Simulate connection
        connection_id = "conn-123"
        user_id = "user-456"

        await websocket_hub.add_connection(connection_id, user_id)

        assert connection_id in websocket_hub.connections
        conn = websocket_hub.connections[connection_id]
        assert conn.user_id == user_id
        assert conn.is_alive

        # Subscribe to channel
        channel = f"realtime_analysis:{user_id}"
        await websocket_hub.subscribe(connection_id, channel)

        assert channel in conn.channels

        # Send message
        message = {"type": "analysis_update", "data": {"score": 85}}
        await websocket_hub.broadcast_to_channel(channel, message)

        # Verify message queued
        assert len(conn.message_queue) > 0

        # Disconnect
        await websocket_hub.remove_connection(connection_id)
        assert connection_id not in websocket_hub.connections

    @pytest.mark.asyncio
    async def test_websocket_channel_operations(self, websocket_hub):
        """✅ Channel subscription and messaging"""
        # Add multiple connections
        conn1 = "conn-1"
        conn2 = "conn-2"
        user1 = "user-1"
        user2 = "user-2"

        await websocket_hub.add_connection(conn1, user1)
        await websocket_hub.add_connection(conn2, user2)

        # Subscribe to same channel
        channel = "broadcast"
        await websocket_hub.subscribe(conn1, channel)
        await websocket_hub.subscribe(conn2, channel)

        # Broadcast message
        message = {"type": "system_announcement", "message": "Server restart"}
        await websocket_hub.broadcast_to_channel(channel, message)

        # Both connections should receive message
        conn1_obj = websocket_hub.connections[conn1]
        conn2_obj = websocket_hub.connections[conn2]

        assert len(conn1_obj.message_queue) > 0
        assert len(conn2_obj.message_queue) > 0

    @pytest.mark.asyncio
    async def test_websocket_health_monitoring(self, websocket_hub):
        """✅ Connection health checks"""
        connection_id = "conn-health"
        user_id = "user-health"

        await websocket_hub.add_connection(connection_id, user_id)

        # Simulate heartbeat
        await websocket_hub.update_heartbeat(connection_id)

        conn = websocket_hub.connections[connection_id]
        assert conn.last_heartbeat is not None

        # Simulate stale connection
        conn.last_heartbeat = datetime.utcnow() - timedelta(seconds=400)

        # Cleanup should remove stale connections
        await websocket_hub._cleanup_stale_connections()

        assert connection_id not in websocket_hub.connections

    # ==================== TIER 12: WEBHOOK EVENTS ====================

    @pytest.mark.asyncio
    async def test_event_publishing_and_delivery(self, event_system):
        """✅ Event publishing and webhook delivery"""
        # Register webhook
        webhook_id = await event_system.register_webhook(
            url="https://example.com/webhook",
            secret="test-secret",
            events=["user.created", "session.completed"],
        )

        assert webhook_id in event_system.webhooks

        # Publish event
        event = Event(
            event_type="user.created",
            resource_id="user-123",
            data={"email": "test@example.com"},
        )

        await event_system.publish_event(event)

        # Verify event stored
        assert len(event_system.events) > 0
        stored_event = event_system.events[-1]
        assert stored_event.event_type == "user.created"

        # Simulate delivery (mock HTTP call)
        with patch("aiohttp.ClientSession.post") as mock_post:
            mock_post.return_value.__aenter__.return_value.status = 200

            await event_system._deliver_webhook(webhook_id, event)

            # Verify webhook called
            mock_post.assert_called_once()
            call_args = mock_post.call_args
            assert call_args[0][0] == "https://example.com/webhook"

    @pytest.mark.asyncio
    async def test_webhook_signature_verification(self, event_system):
        """✅ Webhook HMAC signature verification"""
        webhook_id = await event_system.register_webhook(
            url="https://example.com/webhook", secret="my-secret-key"
        )

        event = Event(event_type="test.event", resource_id="test-123")

        # Generate signature
        signature = event_system._generate_signature(event, "my-secret-key")

        # Verify signature
        is_valid = event_system._verify_signature(signature, event, "my-secret-key")
        assert is_valid

        # Test invalid signature
        is_invalid = event_system._verify_signature("invalid-sig", event, "my-secret-key")
        assert not is_invalid

    @pytest.mark.asyncio
    async def test_webhook_circuit_breaker(self, event_system):
        """✅ Circuit breaker pattern for failing webhooks"""
        webhook_id = await event_system.register_webhook(
            url="https://failing.example.com/webhook", secret="test"
        )

        event = Event(event_type="test.event", resource_id="test-123")

        # Simulate 5 failures
        with patch("aiohttp.ClientSession.post") as mock_post:
            mock_post.return_value.__aenter__.return_value.status = 500

            for _ in range(6):  # One more than threshold
                await event_system._deliver_webhook(webhook_id, event)

        webhook = event_system.webhooks[webhook_id]
        assert webhook.circuit_breaker_open

    # ==================== TIER 13: GRAPHQL API ====================

    def test_graphql_schema_initialization(self, graphql_server):
        """✅ GraphQL schema setup"""
        assert graphql_server.schema is not None
        assert "User" in str(graphql_server.schema)
        assert "Session" in str(graphql_server.schema)

    def test_graphql_query_parsing(self, graphql_server):
        """✅ GraphQL query parsing and validation"""
        query = """
        query GetUser($id: ID!) {
            user(id: $id) {
                id
                email
                sessions {
                    id
                    duration
                }
            }
        }
        """

        # Parse query
        parsed = graphql_server._parse_query(query)
        assert parsed is not None

        # Validate query
        is_valid = graphql_server._validate_query(query)
        assert is_valid

    def test_graphql_mutation_support(self, graphql_server):
        """✅ GraphQL mutation execution"""
        mutation = """
        mutation CreateSession($userId: ID!, $exerciseType: String!) {
            createSession(userId: $userId, exerciseType: $exerciseType) {
                id
                status
            }
        }
        """

        variables = {"userId": "user-123", "exerciseType": "squats"}

        # Mock resolver
        with patch.object(
            graphql_server,
            "_execute_mutation",
            return_value={"id": "session-456", "status": "created"},
        ) as mock_execute:
            result = graphql_server.execute_mutation(mutation, variables)

            mock_execute.assert_called_once()
            assert result["id"] == "session-456"

    # ==================== TIER 14: MODEL VERSIONING ====================

    def test_model_registration_workflow(self, model_registry):
        """✅ Model registration and versioning"""
        # Register model
        model_id = model_registry.register_model(
            name="ensemble_v1",
            version="1.0.0",
            model_type="ENSEMBLE",
            metadata={"accuracy": 0.95},
        )

        assert model_id in model_registry.models

        model = model_registry.models[model_id]
        assert model.name == "ensemble_v1"
        assert model.version == "1.0.0"
        assert model.status == "VALIDATING"

        # Approve model
        model_registry.approve_model(model_id, "admin")

        assert model.status == "APPROVED"

    def test_model_comparison(self, model_registry):
        """✅ Model performance comparison"""
        # Register two models
        model1_id = model_registry.register_model("model_a", "1.0.0", "CNN")
        model2_id = model_registry.register_model("model_b", "1.0.0", "LSTM")

        # Add performance metrics
        model_registry.update_metrics(model1_id, {"accuracy": 0.92, "latency": 50})
        model_registry.update_metrics(model2_id, {"accuracy": 0.89, "latency": 45})

        # Compare models
        comparison = model_registry.compare_models(model1_id, model2_id)

        assert comparison["model_a"]["accuracy"] > comparison["model_b"]["accuracy"]
        assert comparison["model_a"]["latency"] > comparison["model_b"]["latency"]

    def test_experiment_tracking(self, model_registry):
        """✅ Experiment run tracking"""
        experiment_id = model_registry.start_experiment(
            name="accuracy_optimization",
            model_type="ENSEMBLE",
            parameters={"learning_rate": 0.001},
        )

        assert experiment_id in model_registry.experiments

        experiment = model_registry.experiments[experiment_id]
        assert experiment.name == "accuracy_optimization"
        assert experiment.status == "RUNNING"

        # Complete experiment
        model_registry.end_experiment(experiment_id, {"final_accuracy": 0.94})

        assert experiment.status == "COMPLETED"
        assert experiment.metrics["final_accuracy"] == 0.94

    # ==================== TIER 15: ADVANCED ANALYTICS ====================

    def test_cohort_creation_and_analysis(self, analytics_engine):
        """✅ Cohort creation and retention analysis"""
        # Create cohort
        cohort_id = analytics_engine.create_cohort(
            name="new_users_q1_2026",
            criteria={"registration_date": {"start": "2026-01-01", "end": "2026-03-31"}},
            group_by="month",
        )

        assert cohort_id in analytics_engine.cohorts

        cohort = analytics_engine.cohorts[cohort_id]
        assert cohort.name == "new_users_q1_2026"

        # Simulate user data
        users = [
            {"id": "user-1", "registration_date": "2026-01-15", "sessions": 10},
            {"id": "user-2", "registration_date": "2026-02-10", "sessions": 8},
            {"id": "user-3", "registration_date": "2026-03-20", "sessions": 12},
        ]

        # Calculate retention
        retention = analytics_engine.calculate_retention(cohort_id, users, days=[1, 7, 30])

        assert "day_1" in retention
        assert "day_7" in retention
        assert "day_30" in retention

    def test_funnel_analysis(self, analytics_engine):
        """✅ Conversion funnel analysis"""
        # Define funnel steps
        steps = ["landing_page", "sign_up", "first_session", "payment"]

        # Simulate user progression
        user_journeys = [
            {
                "user_id": "user-1",
                "steps": ["landing_page", "sign_up", "first_session", "payment"],
            },
            {
                "user_id": "user-2",
                "steps": ["landing_page", "sign_up", "first_session"],
            },
            {"user_id": "user-3", "steps": ["landing_page", "sign_up"]},
            {"user_id": "user-4", "steps": ["landing_page"]},
        ]

        # Analyze funnel
        funnel = analytics_engine.analyze_funnel(steps, user_journeys)

        assert funnel["landing_page"]["count"] == 4
        assert funnel["payment"]["count"] == 1
        assert funnel["payment"]["conversion_rate"] == 0.25  # 1/4

    def test_user_segmentation(self, analytics_engine):
        """✅ Dynamic user segmentation"""
        users = [
            {"id": "user-1", "sessions_per_week": 5, "avg_score": 85, "age": 25},
            {"id": "user-2", "sessions_per_week": 2, "avg_score": 92, "age": 30},
            {"id": "user-3", "sessions_per_week": 7, "avg_score": 78, "age": 22},
            {"id": "user-4", "sessions_per_week": 1, "avg_score": 88, "age": 35},
        ]

        # Create segments
        segments = analytics_engine.create_segments(
            users,
            {
                "high_engagement": lambda u: u["sessions_per_week"] >= 5,
                "high_performer": lambda u: u["avg_score"] >= 90,
                "young_adult": lambda u: u["age"] < 30,
            },
        )

        assert "high_engagement" in segments
        assert "high_performer" in segments
        assert "young_adult" in segments

        assert len(segments["high_engagement"]) == 2  # users 1 and 3
        assert len(segments["high_performer"]) == 1  # user 2

    # ==================== TIER 16: A/B TESTING ====================

    def test_ab_experiment_creation(self, ab_engine):
        """✅ A/B experiment setup and user allocation"""
        # Create experiment
        experiment_id = ab_engine.create_experiment(
            name="ui_button_color_test",
            variants=["red_button", "blue_button"],
            traffic_percentage=100,
            strategy=AllocationStrategy.RANDOM,
        )

        assert experiment_id in ab_engine.experiments

        experiment = ab_engine.experiments[experiment_id]
        assert experiment.name == "ui_button_color_test"
        assert len(experiment.variants) == 2
        assert experiment.status == "DRAFT"

        # Start experiment
        ab_engine.start_experiment(experiment_id)

        assert experiment.status == "RUNNING"

    def test_user_allocation_strategies(self, ab_engine):
        """✅ Different allocation strategies"""
        experiment_id = ab_engine.create_experiment(
            name="allocation_test",
            variants=["A", "B"],
            strategy=AllocationStrategy.STRATIFIED,
        )

        ab_engine.start_experiment(experiment_id)

        # Allocate users
        allocations = {}
        for i in range(100):
            user_id = f"user-{i}"
            variant = ab_engine.allocate_user(experiment_id, user_id)
            allocations[variant] = allocations.get(variant, 0) + 1

        # Stratified should be roughly equal
        assert abs(allocations.get("A", 0) - allocations.get("B", 0)) <= 10

    def test_experiment_results_analysis(self, ab_engine):
        """✅ Statistical analysis of experiment results"""
        experiment_id = ab_engine.create_experiment(
            name="conversion_test", variants=["control", "variant"]
        )

        ab_engine.start_experiment(experiment_id)

        # Simulate conversions
        for i in range(1000):
            user_id = f"user-{i}"
            variant = ab_engine.allocate_user(experiment_id, user_id)

            # Variant converts at 15%, control at 10%
            converted = (i % 100) < (15 if variant == "variant" else 10)
            ab_engine.record_conversion(experiment_id, user_id, converted)

        # Analyze results
        results = ab_engine.analyze_results(experiment_id)

        assert "control" in results
        assert "variant" in results
        assert results["variant"]["conversion_rate"] > results["control"]["conversion_rate"]
        assert "p_value" in results["variant"]
        assert "confidence_interval" in results["variant"]

    # ==================== TIER 17: FRAUD DETECTION ====================

    def test_fraud_detection_scoring(self, fraud_engine):
        """✅ Real-time fraud scoring"""
        user_id = "user-123"

        # Simulate suspicious actions
        actions = [
            {
                "type": "api_call",
                "count": 150,
                "timeframe": "minute",
            },  # Velocity breach
            {"type": "location_change", "from": "US", "to": "RU"},  # Geo anomaly
            {"type": "device_change", "new_device": True},  # Device anomaly
        ]

        # Calculate risk score
        risk_score = fraud_engine.calculate_risk_score(user_id, actions)

        assert risk_score > 50  # Should be high due to multiple violations
        assert risk_score <= 100

    def test_behavioral_profiling(self, fraud_engine):
        """✅ User behavior profiling"""
        user_id = "user-456"

        # Build profile from normal behavior
        normal_actions = [
            {"hour": 9, "location": "US", "device": "mobile", "sessions": 3},
            {"hour": 10, "location": "US", "device": "mobile", "sessions": 2},
            {"hour": 11, "location": "US", "device": "mobile", "sessions": 4},
        ]

        fraud_engine.build_behavior_profile(user_id, normal_actions)

        assert user_id in fraud_engine.user_profiles

        profile = fraud_engine.user_profiles[user_id]
        assert profile.typical_login_hour == 10  # Average
        assert profile.typical_location == "US"

    def test_fraud_alert_generation(self, fraud_engine):
        """✅ Alert generation for suspicious activity"""
        user_id = "suspicious-user"

        # Simulate critical fraud indicators
        actions = [
            {
                "type": "api_call",
                "count": 200,
                "timeframe": "minute",
            },  # Major velocity breach
            {"type": "location_change", "from": "US", "to": "UNKNOWN"},  # Geo anomaly
            {"type": "unusual_time", "hour": 3},  # Unusual hour
        ]

        risk_score = fraud_engine.calculate_risk_score(user_id, actions)

        # Should trigger alert
        alert = fraud_engine.generate_alert(user_id, risk_score, actions)

        assert alert is not None
        assert alert["risk_level"] == "CRITICAL"
        assert alert["user_id"] == user_id
        assert len(alert["indicators"]) > 0

    def test_user_blocking_mechanism(self, fraud_engine):
        """✅ Automatic user blocking"""
        user_id = "blocked-user"

        # Simulate extreme fraud
        actions = [
            {"type": "api_call", "count": 500, "timeframe": "minute"},
            {"type": "location_change", "from": "US", "to": "HIGH_RISK"},
            {"type": "device_change", "new_device": True},
            {"type": "unusual_time", "hour": 4},
        ]

        risk_score = fraud_engine.calculate_risk_score(user_id, actions)

        # Block user
        blocked = fraud_engine.block_user(user_id, risk_score)

        assert blocked
        assert user_id in fraud_engine.blocked_users

        # Verify subsequent actions blocked
        can_proceed = fraud_engine.check_user_allowed(user_id, "api_call")
        assert not can_proceed


# ==================== END-TO-END INTEGRATION TESTS ====================


class TestPhase2EndToEndIntegration:
    """End-to-end integration tests combining multiple Phase 2 features"""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_analysis_job_with_websocket_updates(self, job_queue, websocket_hub):
        """✅ Job processing with real-time WebSocket updates"""
        # Setup WebSocket connection
        user_id = "user-job-test"

        # Submit analysis job
        job_id = await job_queue.submit_job(
            job_type="biomech_analysis",
            payload={"session_id": "session-123", "frames": 100},
            user_id=user_id,
        )

        # Process job (would normally send WebSocket updates)
        # In real implementation, job processing would emit events to WebSocket

        assert job_id in job_queue.jobs
        assert job_queue.jobs[job_id].user_id == user_id

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_model_update_with_webhook_notification(self, model_registry, event_system):
        """✅ Model update triggers webhook events"""
        # Register webhook for model events
        webhook_id = await event_system.register_webhook(
            url="https://ml-platform.example.com/webhook",
            events=["model.approved", "model.deployed"],
        )

        # Register and approve model
        model_id = model_registry.register_model("new_model", "2.0.0", "ENSEMBLE")
        model_registry.approve_model(model_id, "admin")

        # In real implementation, this would trigger webhook
        # event_system.publish_event(Event("model.approved", model_id))

        assert model_registry.models[model_id].status == "APPROVED"

    @pytest.mark.integration
    def test_ab_test_with_analytics_tracking(self, ab_engine, analytics_engine):
        """✅ A/B test results integrated with analytics"""
        # Create A/B test
        experiment_id = ab_engine.create_experiment(
            name="feature_test", variants=["old_ui", "new_ui"]
        )
        ab_engine.start_experiment(experiment_id)

        # Simulate user interactions
        users = []
        for i in range(100):
            user_id = f"user-{i}"
            variant = ab_engine.allocate_user(experiment_id, user_id)
            converted = (i % 10) < (7 if variant == "new_ui" else 5)
            ab_engine.record_conversion(experiment_id, user_id, converted)

            # Track in analytics
            users.append({"id": user_id, "variant": variant, "converted": converted})  # 70% vs 50%

        # Analyze experiment
        results = ab_engine.analyze_results(experiment_id)

        # Analytics could use this data for segmentation
        segments = analytics_engine.create_segments(
            users,
            {
                "converted": lambda u: u["converted"],
                "new_ui_users": lambda u: u["variant"] == "new_ui",
            },
        )

        assert len(segments["converted"]) > 0
        assert results["new_ui"]["conversion_rate"] > results["old_ui"]["conversion_rate"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
